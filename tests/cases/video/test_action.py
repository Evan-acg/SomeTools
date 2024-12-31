import os
import pytest
from unittest.mock import MagicMock
import send2trash
from app.modules.video.action import (
    ActionOptions,
    RemoveCacheAction,
    BrandMarkerAction,
    RemoveOldFileAction,
    RenameAction,
)


@pytest.fixture
def options():
    return ActionOptions(
        verbose=True,
        input_path="input.txt",
        output_path="output.txt",
        swap_path="swap.txt",
        clean=True,
        swap=True,
    )


def test_remove_cache_action(mocker, options):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("send2trash.send2trash")
    action = RemoveCacheAction()
    assert action(options) is True
    send2trash.send2trash.assert_called_once_with(options.output_path)


def test_remove_cache_action_not_met(mocker, options):
    mocker.patch("os.path.exists", return_value=False)
    action = RemoveCacheAction()
    assert action(options) is False


def test_brand_marker_action(mocker, options):
    mocker.patch("os.path.exists", return_value=True)
    mock_marker = mocker.patch(
        "app.modules.video.marker.Marker.brand", return_value=True
    )
    action = BrandMarkerAction()
    assert action(options) is True
    mock_marker.assert_called_once_with(options.output_path)


def test_brand_marker_action_not_met(mocker, options):
    mocker.patch("os.path.exists", return_value=False)
    action = BrandMarkerAction()
    assert action(options) is False


def test_remove_old_file_action(mocker, options):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("send2trash.send2trash")
    action = RemoveOldFileAction()
    assert action(options) is True
    send2trash.send2trash.assert_called_once_with(options.input_path)


def test_remove_old_file_action_not_met(mocker, options):
    mocker.patch("os.path.exists", return_value=False)
    action = RemoveOldFileAction()
    assert action(options) is False


def test_rename_action(mocker, options):
    mocker.patch("os.path.exists", side_effect=lambda path: path != options.swap_path)
    mocker.patch("os.rename")
    action = RenameAction()
    assert action(options) is True
    os.rename.assert_called_once_with(options.output_path, options.swap_path)


def test_rename_action_not_met(mocker, options):
    mocker.patch("os.path.exists", side_effect=lambda path: path == options.swap_path)
    action = RenameAction()
    assert action(options) is False


def test_remove_cache_action_exception(mocker, options):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("send2trash.send2trash", side_effect=Exception("Test Exception"))
    action = RemoveCacheAction()
    assert action(options) is False

def test_brand_marker_action_exception(mocker, options):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("app.modules.video.marker.Marker.brand", side_effect=Exception("Test Exception"))
    action = BrandMarkerAction()
    assert action(options) is False

def test_remove_old_file_action_exception(mocker, options):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("send2trash.send2trash", side_effect=Exception("Test Exception"))
    action = RemoveOldFileAction()
    assert action(options) is False

def test_rename_action_exception(mocker, options):
    mocker.patch("os.path.exists", side_effect=lambda path: path != options.swap_path)
    mocker.patch("os.rename", side_effect=Exception("Test Exception"))
    action = RenameAction()
    assert action(options) is False

def test_remove_cache_action_verbose(mocker, options):
    options.verbose = True
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("send2trash.send2trash")
    mock_logger = mocker.patch("app.modules.video.action.logger.info")
    action = RemoveCacheAction()
    assert action(options) is True
    mock_logger.assert_called_with(f"Removing <from = {options.output_path}>")

def test_brand_marker_action_verbose(mocker, options):
    options.verbose = True
    mocker.patch("os.path.exists", return_value=True)
    mock_marker = mocker.patch("app.modules.video.marker.Marker.brand", return_value=True)
    mock_logger = mocker.patch("app.modules.video.action.logger.info")
    action = BrandMarkerAction()
    assert action(options) is True
    mock_logger.assert_any_call(f"Branding <from = {options.output_path}>")
    mock_logger.assert_any_call(f"Branding <status = {True}>")

def test_remove_old_file_action_verbose(mocker, options):
    options.verbose = True
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("send2trash.send2trash")
    mock_logger = mocker.patch("app.modules.video.action.logger.info")
    action = RemoveOldFileAction()
    assert action(options) is True
    mock_logger.assert_called_with(f"Removing <from = {options.input_path}>")

def test_rename_action_verbose(mocker, options):
    options.verbose = True
    mocker.patch("os.path.exists", side_effect=lambda path: path != options.swap_path)
    mocker.patch("os.rename")
    mock_logger = mocker.patch("app.modules.video.action.logger.info")
    action = RenameAction()
    assert action(options) is True
    mock_logger.assert_called_with(f"Renaming <from = {options.output_path}, to = {options.swap_path}>")
