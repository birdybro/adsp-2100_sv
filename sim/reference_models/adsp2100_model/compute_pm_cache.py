"""Composed original ADSP-2100 Type 5/cache transaction model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .compute_pm import (
    ComputePMCycleResult,
    ComputePMState,
    apply_compute_pm_cycle,
)
from .instruction_cache import (
    InstructionCacheState,
    apply_instruction_cache_cycle,
    lookup_instruction_cache,
)
from .model import ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup
from .registers import DREGWrite


@dataclass(frozen=True)
class ComputePMCacheState:
    core: ComputePMState = field(default_factory=ComputePMState.reset)
    cache: InstructionCacheState = field(
        default_factory=InstructionCacheState.reset
    )
    pending_cache_instruction: ExactWord | None = None

    @classmethod
    def reset(cls) -> "ComputePMCacheState":
        return cls()


@dataclass(frozen=True)
class ComputePMCacheCycleResult:
    state: ComputePMCacheState
    core: ComputePMCycleResult
    lookup_address_hit: bool = False
    lookup_instruction: int = 0
    lookup_instruction_known: bool = False
    cache_fill: bool = False
    cache_fill_from_recovery: bool = False
    external_fill_selected: bool = False
    cache_fill_accepted: bool = False
    cache_region_restarted: bool = False
    cache_oldest_replaced: bool = False
    external_fill_conflict: bool = False
    integration_conflict: bool = False
    next_instruction: int = 0
    next_instruction_known: bool = False
    instruction_from_cache: bool = False
    instruction_from_external: bool = False


def apply_compute_pm_cache_cycle(
    state: ComputePMCacheState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    pm_read_data: ExactWord | object = UNKNOWN,
    next_fetch_address: ExactWord | object = UNKNOWN,
    force_instruction_fetch: bool = False,
    pm_cycle_complete: bool = True,
    external_fetch_fill: bool = False,
    external_fetch_address: ExactWord | object = UNKNOWN,
    external_fetch_instruction: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
) -> ComputePMCacheCycleResult:
    """Apply one cache fill, Type 5 data cycle, or recovery fetch."""

    lookup = lookup_instruction_cache(state.cache, next_fetch_address)
    pm_transaction_active = (
        state.core.recovery is not None or state.core.pending is not None
    )
    setup_count = sum(
        item is not None
        for item in (
            setup_astat,
            setup_mstat,
            setup_dreg,
            setup_af,
            setup_mf,
            setup_dag,
            setup_px,
        )
    )
    external_fill_conflict = (
        not reset
        and external_fetch_fill
        and (pm_transaction_active or execute or setup_count != 0)
    )
    external_fill_selected = (
        not reset and external_fetch_fill and not pm_transaction_active
    )
    suppress_controls = external_fill_selected

    core_result = apply_compute_pm_cycle(
        state.core,
        reset=reset,
        execute=execute and not suppress_controls,
        opcode=opcode,
        pm_read_data=pm_read_data,
        next_fetch_address=next_fetch_address,
        cache_next_instruction_valid=lookup.instruction_valid,
        force_instruction_fetch=force_instruction_fetch,
        pm_cycle_complete=pm_cycle_complete,
        setup_astat=None if suppress_controls else setup_astat,
        setup_mstat=None if suppress_controls else setup_mstat,
        setup_dreg=None if suppress_controls else setup_dreg,
        setup_af=None if suppress_controls else setup_af,
        setup_mf=None if suppress_controls else setup_mf,
        setup_dag=None if suppress_controls else setup_dag,
        setup_px=None if suppress_controls else setup_px,
    )

    cache_fill_from_recovery = (
        not reset
        and core_result.recovery_fetch
        and core_result.instruction_complete
    )
    cache_fill = cache_fill_from_recovery or external_fill_selected
    if cache_fill_from_recovery:
        fill_address: ExactWord | object = (
            ExactWord(14, core_result.pm_address)
            if core_result.pm_address_known
            else UNKNOWN
        )
        fill_instruction: ExactWord | object = (
            ExactWord(24, core_result.fetched_instruction)
            if core_result.fetched_instruction_known
            else UNKNOWN
        )
    else:
        fill_address = external_fetch_address
        fill_instruction = external_fetch_instruction

    cache_result = apply_instruction_cache_cycle(
        state.cache,
        reset=reset,
        fill=cache_fill,
        fetch_address=fill_address,
        fetch_instruction=fill_instruction,
    )

    issue_cache_instruction = (
        lookup.instruction
        if core_result.cache_instruction_selected
        and lookup.instruction_valid
        and isinstance(lookup.instruction, ExactWord)
        else None
    )
    instruction_from_cache = bool(
        core_result.data_action_complete
        and (
            issue_cache_instruction is not None
            or state.pending_cache_instruction is not None
        )
    )
    instruction_from_external = (
        core_result.recovery_fetch
        and core_result.fetched_instruction_known
    )
    if instruction_from_cache:
        cached = (
            issue_cache_instruction
            if issue_cache_instruction is not None
            else state.pending_cache_instruction
        )
        assert isinstance(cached, ExactWord)
        next_instruction = cached.value
    elif instruction_from_external:
        next_instruction = core_result.fetched_instruction
    else:
        next_instruction = 0

    pending_cache_instruction = state.pending_cache_instruction
    if reset or core_result.data_action_complete:
        pending_cache_instruction = None
    elif core_result.accepted:
        pending_cache_instruction = issue_cache_instruction

    return ComputePMCacheCycleResult(
        state=ComputePMCacheState(
            core=core_result.state,
            cache=cache_result.state,
            pending_cache_instruction=pending_cache_instruction,
        ),
        core=core_result,
        lookup_address_hit=lookup.address_hit,
        lookup_instruction=(
            lookup.instruction.value
            if isinstance(lookup.instruction, ExactWord)
            else 0
        ),
        lookup_instruction_known=lookup.instruction_valid,
        cache_fill=cache_fill,
        cache_fill_from_recovery=cache_fill_from_recovery,
        external_fill_selected=external_fill_selected,
        cache_fill_accepted=cache_result.fill_accepted,
        cache_region_restarted=cache_result.region_restarted,
        cache_oldest_replaced=cache_result.oldest_replaced,
        external_fill_conflict=external_fill_conflict,
        integration_conflict=(
            core_result.integration_conflict or external_fill_conflict
        ),
        next_instruction=next_instruction,
        next_instruction_known=(
            instruction_from_cache or instruction_from_external
        ),
        instruction_from_cache=instruction_from_cache,
        instruction_from_external=instruction_from_external,
    )
