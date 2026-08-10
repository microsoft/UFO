import pytest

from importlib import import_module
import os
from pathlib import Path
import sys
from unittest.mock import MagicMock


def _clear_stubbed_ufo_modules():
    for module_name in ("ufo.automator.basic", "ufo.automator", "ufo"):
        module = sys.modules.get(module_name)
        if module is not None and getattr(module, "__file__", None) is None:
            sys.modules.pop(module_name, None)


def _path_validator_module():
    _clear_stubbed_ufo_modules()
    return import_module("ufo.automator.path_validator")


def test_validate_save_path_rejects_raw_parent_traversal_without_document_dir():
    with pytest.raises(ValueError, match="traversal"):
        _path_validator_module().validate_save_path("../outside")


def test_validate_save_path_rejects_absolute_directory_outside_document_dir(tmp_path):
    document_dir = tmp_path / "Documents"
    outside_dir = tmp_path / "Word" / "STARTUP"
    document_dir.mkdir()
    outside_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_path(
            str(outside_dir), str(document_dir)
        )


def test_validate_save_path_rejects_same_prefix_sibling_directory(tmp_path):
    document_dir = tmp_path / "Documents"
    outside_dir = tmp_path / "Documents-Archive"
    document_dir.mkdir()
    outside_dir.mkdir()

    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_path(
            str(outside_dir), str(document_dir)
        )


def test_validate_save_path_allows_document_directory(tmp_path):
    document_dir = tmp_path / "Documents"
    document_dir.mkdir()

    result = _path_validator_module().validate_save_path(
        str(document_dir), str(document_dir)
    )

    assert Path(result) == document_dir.resolve()


def test_validate_save_path_allows_relative_descendant(tmp_path):
    document_dir = tmp_path / "Documents"
    nested_dir = document_dir / "Exports"
    nested_dir.mkdir(parents=True)

    result = _path_validator_module().validate_save_path(
        "Exports", str(document_dir)
    )

    assert Path(result) == nested_dir.resolve()


def test_validate_save_path_empty_without_document_dir_returns_cwd():
    assert _path_validator_module().validate_save_path("", None) == str(Path.cwd())


def test_validate_save_path_empty_validates_windows_sensitive_document_dir():
    with pytest.raises(ValueError, match="sensitive"):
        _path_validator_module().validate_save_path("", r"C:\Windows")


def test_windows_outside_drive_path_is_rejected():
    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_path(
            r"D:\Temp\evil",
            r"C:\Users\Alice\Documents",
        )


def test_windows_same_prefix_sibling_is_rejected_case_insensitively():
    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_path(
            r"c:\users\alice\Documents-Archive",
            r"C:\Users\Alice\Documents",
        )


def test_windows_relative_descendant_resolves_from_document_dir():
    assert _path_validator_module().validate_save_path(
        "Exports",
        r"C:\Users\Alice\Documents",
    ) == r"C:\Users\Alice\Documents\Exports"


def test_windows_same_prefix_non_sensitive_path_is_allowed():
    assert _path_validator_module().validate_path_not_sensitive(
        r"C:\Windows-Archive"
    ) == r"C:\Windows-Archive"


@pytest.mark.parametrize(
    "path_str",
    [
        r"C:\Windows\System32",
        r"C:\Program Files\App",
        r"C:\ProgramData\Vendor",
    ],
)
def test_windows_sensitive_paths_are_rejected_independent_of_host(path_str):
    with pytest.raises(ValueError, match="sensitive"):
        _path_validator_module().validate_path_not_sensitive(path_str)


@pytest.mark.skipif(os.name != "nt", reason="Windows-only rooted path semantics")
def test_windows_forward_slash_rooted_sensitive_path_is_rejected():
    with pytest.raises(ValueError, match="sensitive"):
        _path_validator_module().validate_path_not_sensitive("/Windows/System32")


def test_windows_drive_relative_path_on_same_drive_resolves_within_document_dir():
    assert _path_validator_module().validate_save_path(
        r"C:Exports",
        r"C:\Users\Alice\Documents",
    ) == r"C:\Users\Alice\Documents\Exports"


def test_windows_drive_relative_path_on_other_drive_is_rejected():
    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_path(
            r"D:Exports",
            r"C:\Users\Alice\Documents",
        )


def test_windows_rooted_path_without_drive_is_rejected():
    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_path(
            r"\Temp",
            r"C:\Users\Alice\Documents",
        )


def test_windows_unc_descendant_is_allowed():
    assert _path_validator_module().validate_save_path(
        r"Exports",
        r"\\server\share\Docs",
    ) == r"\\server\share\Docs\Exports"


def test_windows_unc_cross_share_is_rejected():
    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_path(
            r"\\server\other\evil",
            r"\\server\share\Docs",
        )


def test_windows_mixed_separators_descendant_is_allowed():
    assert _path_validator_module().validate_save_path(
        r"Exports/final",
        r"C:\Users\Alice\Documents",
    ) == r"C:\Users\Alice\Documents\Exports\final"


def test_validate_save_file_path_allows_normal_docx_path(tmp_path):
    document_dir = tmp_path / "Documents"
    document_dir.mkdir()

    result = _path_validator_module().validate_save_file_path(
        str(document_dir),
        "Proposal",
        ".docx",
        str(document_dir),
    )

    assert Path(result) == (document_dir / "Proposal.docx").resolve()


def test_validate_save_file_path_allows_relative_subdirectory(tmp_path):
    document_dir = tmp_path / "Documents"
    nested_dir = document_dir / "Exports"
    nested_dir.mkdir(parents=True)

    result = _path_validator_module().validate_save_file_path(
        "Exports",
        "Proposal",
        ".docx",
        str(document_dir),
    )

    assert Path(result) == (nested_dir / "Proposal.docx").resolve()


def test_validate_save_file_path_allows_macro_enabled_extension(tmp_path):
    document_dir = tmp_path / "Documents"
    document_dir.mkdir()

    result = _path_validator_module().validate_save_file_path(
        str(document_dir),
        "MacroEnabled",
        ".dotm",
        str(document_dir),
    )

    assert Path(result) == (document_dir / "MacroEnabled.dotm").resolve()


@pytest.mark.parametrize(
    ("component_name", "control_char"),
    [
        ("file_name", "\x01"),
        ("file_name", "\x1f"),
        ("file_ext", "\x02"),
        ("file_ext", "\x1e"),
    ],
)
def test_validate_save_file_path_rejects_windows_ascii_control_characters(
    tmp_path,
    component_name,
    control_char,
):
    document_dir = tmp_path / "Documents"
    document_dir.mkdir()
    file_name = "Proposal"
    file_ext = ".docx"

    if component_name == "file_name":
        file_name = f"bad{control_char}name"
    else:
        file_ext = f".{control_char}docx"

    with pytest.raises(ValueError):
        _path_validator_module().validate_save_file_path(
            str(document_dir),
            file_name,
            file_ext,
            str(document_dir),
        )


@pytest.mark.parametrize(
    ("file_name", "file_ext"),
    [
        ("../../outside/evil", ".dotm"),
        (r"..\\..\\outside\\evil", ".dotm"),
        (r"C:\\Temp\\evil", ".docm"),
        ("evil", r".docx\\payload"),
        ("evil", "docx"),
        ("CON", ".docx"),
        ("PRN.txt", ".docx"),
        ("Proposal.", ".docx"),
        ("Proposal ", ".docx"),
        ("Proposal", ".docx "),
        ("Propo?sal", ".docx"),
        ("", ".docx"),
        ("Proposal", ""),
    ],
)
def test_validate_save_file_path_rejects_path_like_leaf_components(
    tmp_path,
    file_name,
    file_ext,
):
    document_dir = tmp_path / "Documents"
    document_dir.mkdir()

    with pytest.raises(ValueError):
        _path_validator_module().validate_save_file_path(
            str(document_dir),
            file_name,
            file_ext,
            str(document_dir),
        )


def test_validate_save_file_path_rejects_final_path_outside_base(tmp_path):
    document_dir = tmp_path / "Documents"
    outside_dir = tmp_path / "Outside"
    linked_dir = document_dir / "LinkedOutside"
    document_dir.mkdir()
    outside_dir.mkdir()

    try:
        linked_dir.symlink_to(outside_dir, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not available in this environment")

    with pytest.raises(ValueError, match="outside"):
        _path_validator_module().validate_save_file_path(
            str(linked_dir),
            "Proposal",
            ".docx",
            str(document_dir),
        )


@pytest.mark.parametrize(
    ("module_name", "class_name", "file_ext"),
    [
        ("ufo.automator.app_apis.word.wordclient", "WordWinCOMReceiver", ".dotm"),
        ("ufo.automator.app_apis.excel.excelclient", "ExcelWinCOMReceiver", ".xlsm"),
        (
            "ufo.automator.app_apis.powerpoint.powerpointclient",
            "PowerPointWinCOMReceiver",
            ".pptx",
        ),
        (
            "ufo.automator.app_apis.powerpoint.powerpointclient",
            "PowerPointWinCOMReceiver",
            ".png",
        ),
    ],
)
def test_save_as_rejects_filename_traversal_before_office_call(
    tmp_path, module_name, class_name, file_ext
):
    document_dir = tmp_path / "Documents"
    document_dir.mkdir()

    _clear_stubbed_ufo_modules()
    receiver_class = getattr(import_module(module_name), class_name)
    receiver = object.__new__(receiver_class)
    receiver.com_object = MagicMock()
    receiver.com_object.FullName = str(document_dir / ("source" + file_ext))
    receiver.com_object.Slides.Count = 1
    receiver.com_object.Slides.return_value = MagicMock()

    with pytest.raises(ValueError):
        receiver.save_as(
            file_dir="",
            file_name=r"..\\..\\Word\\STARTUP\\evil",
            file_ext=file_ext,
        )

    receiver.com_object.SaveAs.assert_not_called()
    receiver.com_object.Slides.return_value.Export.assert_not_called()