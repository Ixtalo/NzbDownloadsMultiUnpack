# -*- coding: utf-8 -*-
"""Unit tests."""

# pylint: disable=missing-class-docstring,missing-function-docstring

from datetime import datetime
from pathlib import Path
import pytest
from nzbdownloadsmultiunpack import multiunpackrecursive
from nzbdownloadsmultiunpack.multiunpackrecursive import \
    ArchiverRar, Archiver7z, _construct_quoted, main, \
    __version__, __updated__

FILENAMES = [
    "volume1.part1.rar",
    "volume1.part2.rar",
    "volume1.part3.rar",

    # single RAR
    "volume2.single.rar",

    # starting at 0
    "volume3.part0.rar",
    "volume3.part1.rar",
    "volume3.part2.rar",

    # more 0s
    "volume4.part001.rar",
    "volume4.part002.rar",
    "volume4.part003.rar",

    # v4 naming scheme
    "volume5.rar",
    "volume5.r00",
    "volume5.r01",

    # starting at 0
    "volume6.part00000.rar",
    "volume6.part00001.rar",
    "volume6.part00002.rar",

    # 7z multi-volume
    "volume7.7z.001",
    "volume7.7z.002",
    "volume7.7z.003",

    # 7z single
    "volume8.7z",
]


class TestArchiverRar:

    @staticmethod
    def test_find_archive_files():
        actual = ArchiverRar().find_archive_files(FILENAMES)
        assert actual == {"volume1.part1.rar", "volume2.single.rar", "volume3.part1.rar",
                          "volume4.part001.rar", "volume5.rar", "volume6.part00001.rar"}

    @staticmethod
    def test_get_basename():
        instance = ArchiverRar()
        assert instance.get_basename("xyz") == "xyz"
        assert instance.get_basename("xyz.rar") == "xyz"
        assert instance.get_basename("xyz.part1.rar") == "xyz"
        assert instance.get_basename("xyz.part001.rar") == "xyz"
        assert instance.get_basename("xyz.part000.rar") == "xyz"

    @staticmethod
    def test_build_rm_command():
        instance = ArchiverRar()
        # input is relative path
        assert instance.build_rm_command(Path("xyz.rar")) == \
            f'rm -fv "{Path("xyz.rar").resolve()}" "{Path("xyz.par2").resolve()}"'
        assert instance.build_rm_command(Path("xyz.part1.rar")) == \
            f'rm -fv "{Path("xyz").resolve()}".part*.rar "{Path("xyz.par2").resolve()}"'

        # input is absolute
        assert instance.build_rm_command(Path("xyz.rar").resolve()) == \
            f'rm -fv "{Path("xyz.rar").resolve()}" "{Path("xyz.par2").resolve()}"'
        assert instance.build_rm_command(Path("xyz.part1.rar").resolve()) == \
            f'rm -fv "{Path("xyz").resolve()}".part*.rar "{Path("xyz.par2").resolve()}"'

        # no .rar
        with pytest.raises(AssertionError):
            instance.build_rm_command(Path("xyz.rax"))


class TestArchiver7z:

    @staticmethod
    def test_find_archive_files():
        actual = Archiver7z().find_archive_files(FILENAMES)
        assert actual == {"volume7.7z.001", "volume8.7z"}

    @staticmethod
    def test_get_basename():
        instance = Archiver7z()
        assert instance.get_basename("xyz") == "xyz"
        assert instance.get_basename("xyz.7z") == "xyz"
        assert instance.get_basename("xyz.7z.000") == "xyz"
        assert instance.get_basename("xyz.7z.001") == "xyz"
        assert instance.get_basename("xyz.7z.0") == "xyz"
        assert instance.get_basename("xyz.7z.8") == "xyz"

    @staticmethod
    def test_build_rm_command():
        instance = Archiver7z()
        # input is relative path
        assert instance.build_rm_command(Path("xyz.7z")) == \
            f'rm -fv "{Path("xyz").resolve()}".7z* "{Path("xyz.par2").resolve()}"'
        assert instance.build_rm_command(Path("xyz.7z.001")) == \
            f'rm -fv "{Path("xyz").resolve()}".7z* "{Path("xyz.par2").resolve()}"'

        # input is absolute path
        assert instance.build_rm_command(Path("xyz.7z").resolve()) == \
            f'rm -fv "{Path("xyz").resolve()}".7z* "{Path("xyz.par2").resolve()}"'
        assert instance.build_rm_command(Path("xyz.7z.001").resolve()) == \
            f'rm -fv "{Path("xyz").resolve()}".7z* "{Path("xyz.par2").resolve()}"'

        # no .rar
        with pytest.raises(AssertionError):
            instance.build_rm_command(Path("xyz.7y"))


def test_construct_quoted():
    assert _construct_quoted({"foo", "bar"}) == {'"foo"', '"bar"'}


# https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html#accessing-captured-output-from-a-test-function
def test_main(monkeypatch, capsys):
    """Test the main() method by monkeypatching sys.argv and capturing STDOUT,
    STDERR and logging output."""
    # overwrite/monkeypatch sys.argv
    monkeypatch.setattr("sys.argv", ("foo", "./testdata/",))
    # do action
    main()
    # check
    captured = capsys.readouterr()
    assert captured.err == ""
    lines = captured.out.splitlines()
    assert len(lines) == 7
    assert "sleep" not in captured.out  # too small for cooldown sleep
    assert "../" not in captured.out    # all paths must be absolute
    # first 2 lines are metadata
    now = datetime.now().isoformat()
    assert lines[0].startswith(f"# created by NzbDownloadsMultiUnpack {__version__} ({__updated__}) at {now[:20]}")
    assert lines[1] == "# 2 entries"
    # third and following lines then contain the actual commands block
    assert lines[2] == '# -- 1. --------------------------------------------------'
    assert lines[3].startswith('unrar x -o- -p"foobardir" "/')
    assert 'testdata/rar_example.dir.{{foobardir}}/rand.indir".part*.rar' in lines[3]
    assert 'testdata/rar_example.dir.{{foobardir}}/rand.indir.par2"' in lines[3]
    assert 'testdata/rar_example.dir.{{foobardir}}/" && rm ' in lines[3]
    assert "sleep" not in lines[0]  # too small for cooldown sleep
    assert "../" not in lines[0]    # all paths must be absolute
    assert lines[4] == '# -- 2. --------------------------------------------------'
    assert lines[5].startswith('7z x -aos -o"/')
    assert 'testdata/7z_example.dir.{{foobardir}}/rand.indir".7z*' in lines[5]
    assert 'testdata/7z_example.dir.{{foobardir}}/rand.indir.par2"' in lines[5]
    assert 'testdata/7z_example.dir.{{foobardir}}/rand.indir.7z.001" && rm' in lines[5]


# https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html#accessing-captured-output-from-a-test-function
def test_main_win32(monkeypatch, capsys):
    """Test the main() method by monkeypatching sys.argv and capturing STDOUT,
    STDERR and logging output."""
    # simulate win32
    monkeypatch.setattr(multiunpackrecursive, "_is_ms_windows", lambda: True)
    # overwrite/monkeypatch sys.argv
    monkeypatch.setattr("sys.argv", ("foo", "./testdata/",))
    # do action
    main()
    # check
    captured = capsys.readouterr()
    assert captured.err == ""
    lines = captured.out.splitlines()
    assert len(lines) == 9
    assert "sleep" not in captured.out  # too small for cooldown sleep
    assert "../" not in captured.out    # all paths must be absolute
    # first 2 lines are metadata
    now = datetime.now().isoformat()
    assert lines[0].startswith(f"REM created by NzbDownloadsMultiUnpack {__version__} ({__updated__}) at {now[:20]}")
    assert lines[1] == "REM 2 entries"
    assert lines[2] == "chcp 1252"
    assert lines[3] == "REM --------------------------------------------------"
    # third and following lines then contain the actual commands block
    assert lines[4] == 'REM -- 1. --------------------------------------------------'
    # third and following lines then contain the actual commands
    assert lines[5].startswith('7z x -aos -o"/')
    assert 'testdata/rar_example.dir.{{foobardir}}/rand.indir".part*.rar' in lines[5]
    assert 'testdata/rar_example.dir.{{foobardir}}/rand.indir.par2"' in lines[5]
    assert 'testdata/rar_example.dir.{{foobardir}}/rand.indir.part1.rar" && del /q "/' in lines[5]
    assert lines[6] == 'REM -- 2. --------------------------------------------------'
    assert lines[7].startswith('7z x -aos -o"/')
    assert 'testdata/7z_example.dir.{{foobardir}}/rand.indir".7z*' in lines[7]
    assert 'testdata/7z_example.dir.{{foobardir}}/rand.indir.par2"' in lines[7]
    assert 'testdata/7z_example.dir.{{foobardir}}/rand.indir.7z.001" && del /q "/' in lines[7]
