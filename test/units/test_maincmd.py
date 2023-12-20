import pytest
from udocker.maincmd import main
from udocker.umain import UMain

@pytest.mark.parametrize("argv, raise_exception, expected_exit_status", [
    (["udocker"], None, 0),
    (["udocker"], KeyboardInterrupt, 1),
    (["udocker"], SystemExit(0), 0),
    (["udocker"], SystemExit(1), 1),
    (["udocker"], SystemExit("error"), 1),
])
def test_01_main(mocker, argv, raise_exception, expected_exit_status):
    mocker.patch('sys.argv', argv)

    if not raise_exception:
        mocker.patch('udocker.umain.UMain', return_value=mocker.Mock())
    else:
        mocker.patch.object(UMain, 'execute', side_effect=raise_exception)

    mock_exit = mocker.patch('sys.exit')
    main()
    mock_exit.assert_called_with(expected_exit_status)