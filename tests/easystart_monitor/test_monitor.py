"""Tests for the EasyStart live-frame decode helpers."""

import pytest

from easystart_monitor.monitor import (
    decode_frame,
    dump_indexed,
    dump_raw,
    is_text,
    le16,
    le32,
    parse_args,
)


def make_frame(
    state: int = 0,
    learned: int = 3,
    current: int = 125,
    period: int = 10000,
    peak: int = 312,
    scpt: int = 7,
    faults: int = 2,
    starts: int = 70000,
) -> bytes:
    """Build an 18-byte live frame from raw field values."""
    return (
        bytes([0x10, 0x00, state, learned])
        + current.to_bytes(2, "little")
        + period.to_bytes(2, "little")
        + peak.to_bytes(2, "little")
        + scpt.to_bytes(2, "little")
        + faults.to_bytes(2, "little")
        + starts.to_bytes(4, "little")
    )


def test_le16_reads_little_endian() -> None:
    assert le16(bytes([0x34, 0x12]), 0) == 0x1234


def test_le32_reads_little_endian() -> None:
    assert le32(bytes([0x00, 0x78, 0x56, 0x34, 0x12]), 1) == 0x12345678


def test_frame_is_18_bytes() -> None:
    assert len(make_frame()) == 18


def test_decode_frame_fields() -> None:
    out = decode_frame(make_frame())
    assert "state=Normal" in out
    assert "current= 12.5A" in out
    assert "freq=50.00Hz" in out
    assert "peak= 31.2A" in out
    assert "learned=  3" in out
    assert "scpt=    7" in out
    assert "faults=    2" in out
    assert "starts= 70000" in out


@pytest.mark.parametrize(
    ("state", "text"),
    [(2, "Short Cycle Delay"), (9, "Wrong Voltage Flt"), (10, "Not Defined(10)")],
)
def test_decode_frame_state(state: int, text: str) -> None:
    assert f"state={text}" in decode_frame(make_frame(state=state))


def test_decode_frame_zero_period_reports_zero_frequency() -> None:
    assert "freq= 0.00Hz" in decode_frame(make_frame(period=0))


def test_decode_frame_short() -> None:
    assert decode_frame(bytes(5)) == "(short frame, 5 bytes)"


def test_dump_raw() -> None:
    assert dump_raw(bytes([0x0A, 0xFF])) == "0a ff"


def test_dump_indexed() -> None:
    assert dump_indexed(bytes([0x0A, 0xFF])) == "[ 0]= 10/0x0a  [ 1]=255/0xff"


def test_is_text() -> None:
    assert is_text(b'{"Sts": Success}')
    assert not is_text(make_frame())


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.interval == 1.0
    assert not args.discover
    assert not args.raw


def test_parse_args_list_alias() -> None:
    assert parse_args(["--list"]).discover
