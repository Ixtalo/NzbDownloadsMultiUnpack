from pathlib import Path
import pytest
from multiunpackrecursive import ArchiverRar, Archiver7z, _construct_quoted, main, _is_ms_windows

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
               f'rm "{Path("xyz.rar").resolve()}"'
        assert instance.build_rm_command(Path("xyz.part1.rar")) == \
               f'rm "{Path("xyz").resolve()}".part*.rar'

        # input is absolute
        assert instance.build_rm_command(Path("xyz.rar").resolve()) == \
               f'rm "{Path("xyz.rar").resolve()}"'
        assert instance.build_rm_command(Path("xyz.part1.rar").resolve()) == \
               f'rm "{Path("xyz").resolve()}".part*.rar'

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
               f'rm "{Path("xyz").resolve()}".7z*'
        assert instance.build_rm_command(Path("xyz.7z.001")) == \
               f'rm "{Path("xyz").resolve()}".7z*'

        # input is absolute path
        assert instance.build_rm_command(Path("xyz.7z").resolve()) == \
               f'rm "{Path("xyz").resolve()}".7z*'
        assert instance.build_rm_command(Path("xyz.7z.001").resolve()) == \
               f'rm "{Path("xyz").resolve()}".7z*'

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
    monkeypatch.setattr("sys.argv", ("foo", "../example_data/",))
    # do action
    main()
    # check
    captured = capsys.readouterr()
    assert captured.err == ""
    # pushd tests && python ../video_info.py ./testdata/ 2>/dev/null
    lines = captured.out.splitlines()
    assert len(lines) == 4
    assert lines[0].startswith('unrar x -o- -p"foobardir" "/')
    assert lines[0].endswith('example_data/rar_example.dir.{{foobardir}}/rand.indir".part*.rar')
    assert 'example_data/rar_example.dir.{{foobardir}}/" && rm ' in lines[0]
    assert "sleep" not in lines[0]  # too small for cooldown sleep
    assert "../" not in lines[0]    # all paths must be absolute
    assert lines[1] == '#  ------------------------------------------------------------'
    assert lines[2].startswith('7z x -aos -o"/')
    assert lines[2].endswith('example_data/7z_example.dir.{{foobardir}}/rand.indir".7z*')
    assert 'example_data/7z_example.dir.{{foobardir}}/rand.indir.7z.001" && rm' in lines[2]
    assert "sleep" not in lines[2]  # too small for cooldown sleep
    assert "../" not in lines[2]    # all paths must be absolute
    assert lines[3] == '#  ------------------------------------------------------------'



# https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html#accessing-captured-output-from-a-test-function
def test_main_win32(monkeypatch, capsys):
    """Test the main() method by monkeypatching sys.argv and capturing STDOUT,
    STDERR and logging output."""
    # simulate win32
    monkeypatch.setattr("multiunpackrecursive._is_ms_windows", lambda: True)
    # overwrite/monkeypatch sys.argv
    monkeypatch.setattr("sys.argv", ("foo", "../example_data/",))
    # do action
    main()
    # check
    captured = capsys.readouterr()
    assert captured.err == ""
    # pushd tests && python ../video_info.py ./testdata/ 2>/dev/null
    lines = captured.out.splitlines()
    assert len(lines) == 4
    assert lines[0].startswith('7z x -aos -o"/')
    assert lines[0].endswith('example_data/rar_example.dir.{{foobardir}}/rand.indir".part*.rar')
    assert 'example_data/rar_example.dir.{{foobardir}}/rand.indir.part1.rar" && del /q "/' in lines[0]
    assert "sleep" not in lines[0]  # too small for cooldown sleep
    assert "../" not in lines[0]    # all paths must be absolute
    assert lines[1] == 'REM  ------------------------------------------------------------'
    assert lines[2].startswith('7z x -aos -o"/')
    assert lines[2].endswith('example_data/7z_example.dir.{{foobardir}}/rand.indir".7z*')
    assert 'example_data/7z_example.dir.{{foobardir}}/rand.indir.7z.001" && del /q "/' in lines[2]
    assert "sleep" not in lines[2]  # too small for cooldown sleep
    assert "../" not in lines[2]    # all paths must be absolute
    assert lines[3] == 'REM  ------------------------------------------------------------'
