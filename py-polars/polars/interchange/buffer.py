from __future__ import annotations

from typing import TYPE_CHECKING

from polars.interchange.protocol import DlpackDeviceType, DtypeKind
from polars.interchange.utils import polars_dtype_to_dtype

if TYPE_CHECKING:
    from typing import NoReturn

    from polars import Series


class PolarsBuffer:
    """A buffer backed by a Polars Series consisting of a single chunk."""

    def __init__(self, data: Series, *, allow_copy: bool = True):
        if data.n_chunks() > 1:
            if not allow_copy:
                raise RuntimeError(
                    "non-contiguous buffer must be made contiguous, which is not zero-copy"
                )
            data = data.rechunk()

        self._data = data

    @property
    def bufsize(self) -> int:
        """Buffer size in bytes."""
        dtype = polars_dtype_to_dtype(self._data.dtype)

        if dtype[0] == DtypeKind.STRING:
            return self._data.str.lengths().sum()  # type: ignore[return-value]

        n_bits = self._data.len() * dtype[1]

        result, rest = divmod(n_bits, 8)
        # Round up to the nearest byte
        if rest:
            return result + 1
        else:
            return result

    @property
    def ptr(self) -> int:
        """Pointer to start of the buffer as an integer."""
        _offset, _length, pointer = self._data._s.get_ptr()
        return pointer

    def __dlpack__(self) -> NoReturn:
        """Represent this structure as DLPack interface."""
        raise NotImplementedError("__dlpack__")

    def __dlpack_device__(self) -> tuple[DlpackDeviceType, None]:
        """Device type and device ID for where the data in the buffer resides."""
        return (DlpackDeviceType.CPU, None)

    def __repr__(self) -> str:
        bufsize = self.bufsize
        ptr = self.ptr
        device = self.__dlpack_device__()[0].name
        return f"PolarsBuffer(bufsize={bufsize}, ptr={ptr}, device={device!r})"
