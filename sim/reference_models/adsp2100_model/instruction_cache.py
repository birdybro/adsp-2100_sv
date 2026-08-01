"""Independent functional model of the original ADSP-2100 instruction cache.

The original cache is a 16 by 24-bit array addressed by PMA[3:0].  Its monitor
accepts only one contiguous program-memory region at a time.  Sequential fills
extend that region and, once full, replace its oldest word.  A discontinuous
external instruction fetch starts a new one-word region.

The manual describes hidden ahead/behind monitor registers but not their exact
bit-level transitions.  This model therefore represents the documented
observable contiguous-region contract, not an inferred microarchitecture.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import ExactWord, UNKNOWN


CACHE_WORDS = 16
PM_ADDRESS_MASK = 0x3FFF


@dataclass(frozen=True)
class InstructionCacheState:
    words: tuple[ExactWord | object, ...] = (UNKNOWN,) * CACHE_WORDS
    data_valid: tuple[bool, ...] = (False,) * CACHE_WORDS
    region_start: int = 0
    region_count: int = 0

    @classmethod
    def reset(cls) -> "InstructionCacheState":
        return cls()


@dataclass(frozen=True)
class InstructionCacheLookup:
    address_hit: bool
    instruction: ExactWord | object

    @property
    def instruction_valid(self) -> bool:
        return self.address_hit and isinstance(self.instruction, ExactWord)


@dataclass(frozen=True)
class InstructionCacheCycleResult:
    state: InstructionCacheState
    fill_accepted: bool = False
    region_restarted: bool = False
    oldest_replaced: bool = False


def _known_address(address: ExactWord | object) -> int | None:
    if not isinstance(address, ExactWord):
        return None
    if address.width != 14:
        raise ValueError("cache address must be exactly 14 bits")
    return address.value


def _known_instruction(word: ExactWord | object) -> ExactWord | None:
    if not isinstance(word, ExactWord):
        return None
    if word.width != 24:
        raise ValueError("cached instruction must be exactly 24 bits")
    return word


def cache_region_contains(state: InstructionCacheState, address: int) -> bool:
    if not 0 <= address <= PM_ADDRESS_MASK:
        raise ValueError("cache address must fit 14 bits")
    if not 0 <= state.region_count <= CACHE_WORDS:
        raise ValueError("cache region count is invalid")
    if state.region_count == 0:
        return False
    delta = (address - state.region_start) & PM_ADDRESS_MASK
    return delta < state.region_count


def lookup_instruction_cache(
    state: InstructionCacheState,
    address: ExactWord | object,
) -> InstructionCacheLookup:
    known_address = _known_address(address)
    if known_address is None or not cache_region_contains(state, known_address):
        return InstructionCacheLookup(False, UNKNOWN)
    index = known_address & 0xF
    instruction = state.words[index] if state.data_valid[index] else UNKNOWN
    return InstructionCacheLookup(True, instruction)


def apply_instruction_cache_cycle(
    state: InstructionCacheState,
    *,
    reset: bool = False,
    fill: bool = False,
    fetch_address: ExactWord | object = UNKNOWN,
    fetch_instruction: ExactWord | object = UNKNOWN,
) -> InstructionCacheCycleResult:
    """Apply one external instruction-fetch completion.

    An unknown fill address invalidates monitor validity rather than assigning
    an invented cache slot.  Unknown instruction data retains the documented
    address region but marks that slot unusable in this deterministic model.
    """

    if reset:
        return InstructionCacheCycleResult(InstructionCacheState.reset())
    if not fill:
        return InstructionCacheCycleResult(state)

    address = _known_address(fetch_address)
    instruction = _known_instruction(fetch_instruction)
    if address is None:
        return InstructionCacheCycleResult(
            InstructionCacheState(
                state.words,
                (False,) * CACHE_WORDS,
                0,
                0,
            ),
            region_restarted=True,
        )

    words = list(state.words)
    valid = list(state.data_valid)
    count = state.region_count
    start = state.region_start
    contained = cache_region_contains(state, address)
    append_address = (start + count) & PM_ADDRESS_MASK
    restarted = False
    replaced = False

    if count == 0:
        valid = [False] * CACHE_WORDS
        start = address
        count = 1
        restarted = True
    elif contained:
        pass
    elif address == append_address:
        if count < CACHE_WORDS:
            count += 1
        else:
            valid[start & 0xF] = False
            start = (start + 1) & PM_ADDRESS_MASK
            replaced = True
    else:
        valid = [False] * CACHE_WORDS
        start = address
        count = 1
        restarted = True

    index = address & 0xF
    words[index] = instruction if instruction is not None else UNKNOWN
    valid[index] = instruction is not None
    return InstructionCacheCycleResult(
        InstructionCacheState(tuple(words), tuple(valid), start, count),
        fill_accepted=True,
        region_restarted=restarted,
        oldest_replaced=replaced,
    )
