import contextlib
import os.path
import unittest
import unittest.mock

import xdg.BaseDirectory

import aioxmpp.errors
import aioxmpp.utils as aioxmpp_utils

import mlxc.utils as utils


class Test_imports_from_aioxmpp(unittest.TestCase):
    def test_imports(self):
        self.assertIs(
            utils.namespaces,
            aioxmpp_utils.namespaces
        )


class Testmlxc_namespaces(unittest.TestCase):
    def test_account_namespace(self):
        self.assertEqual(
            "https://xmlns.zombofant.net/mlxc/core/account/1.0",
            utils.mlxc_namespaces.account
        )

    def test_roster_namespace(self):
        self.assertEqual(
            "https://xmlns.zombofant.net/mlxc/core/roster/1.0",
            utils.mlxc_namespaces.roster
        )


class Testmultiopen(unittest.TestCase):
    def setUp(self):
        self.paths = [
            "/foo/bar",
            "/baz",
            "/fnord",
        ]

    def test_first_success(self):
        mode = object()
        encoding = object()
        obj = object()

        with contextlib.ExitStack() as stack:
            open_ = stack.enter_context(unittest.mock.patch(
                "builtins.open"
            ))
            open_.return_value = obj

            result = utils.multiopen(
                self.paths,
                "foo.xml",
                mode,
                encoding=encoding)

        self.assertIs(
            result,
            obj)

        self.assertSequenceEqual(
            open_.mock_calls,
            [
                unittest.mock.call(
                    os.path.join(self.paths[0], "foo.xml"),
                    mode,
                    encoding=encoding)
            ]
        )

    def test_tries_and_returns_first_success(self):
        mode = object()
        encoding = object()
        obj = object()

        excs = [FileNotFoundError() for i in range(len(self.paths)-1)]
        excs_to_use = list(excs)
        call_rec = unittest.mock.Mock()

        def open_mock(*args, **kwargs):
            call_rec(*args, **kwargs)
            if excs_to_use:
                raise excs_to_use.pop(0)
            return obj

        with contextlib.ExitStack() as stack:
            open_ = stack.enter_context(unittest.mock.patch(
                "builtins.open",
                open_mock
            ))

            result = utils.multiopen(
                self.paths,
                "foo.xml",
                mode,
                encoding=encoding)

        self.assertSequenceEqual(
            call_rec.mock_calls,
            [
                unittest.mock.call(
                    os.path.join(path, "foo.xml"),
                    mode,
                    encoding=encoding)
                for path in self.paths
            ]
        )


class Testxdgopen_generic(unittest.TestCase):
    def test_open_r(self):
        paths = ["/foo/bar", "/fnord", "/baz"]

        base = unittest.mock.Mock()
        base.load_paths.return_value = iter(paths)
        resource = ["foo", "bar"]
        encoding = object()

        with unittest.mock.patch("mlxc.utils.multiopen") as multiopen:
            utils.xdgopen_generic(
                resource,
                "foo.xml",
                "rb",
                load_paths=base.load_paths,
                save_path=base.save_path,
                encoding=encoding
            )

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.load_paths(*resource),
            ]
        )

        self.assertSequenceEqual(
            multiopen.mock_calls,
            [
                unittest.mock.call(
                    list(reversed(paths)),
                    "foo.xml",
                    mode="rb",
                    encoding=encoding
                )
            ]
        )

    def test_open_w(self):
        path = "/foo/bar"

        base = unittest.mock.Mock()
        base.save_path.return_value = path
        resource = ["foo", "bar"]
        encoding = object()

        with unittest.mock.patch("builtins.open") as open_:
            utils.xdgopen_generic(
                resource,
                "foo.xml",
                "wb",
                load_paths=base.load_paths,
                save_path=base.save_path,
                encoding=encoding
            )

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.save_path(*resource),
            ]
        )

        self.assertSequenceEqual(
            open_.mock_calls,
            [
                unittest.mock.call(
                    os.path.join(path, "foo.xml"),
                    mode="wb",
                    encoding=encoding
                )
            ]
        )

    def test_open_a(self):
        path = "/foo/bar"

        base = unittest.mock.Mock()
        base.save_path.return_value = path
        resource = ["foo", "bar"]
        encoding = object()

        with unittest.mock.patch("builtins.open") as open_:
            utils.xdgopen_generic(
                resource,
                "foo.xml",
                "ab",
                load_paths=base.load_paths,
                save_path=base.save_path,
                encoding=encoding
            )

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.save_path(*resource),
            ]
        )

        self.assertSequenceEqual(
            open_.mock_calls,
            [
                unittest.mock.call(
                    os.path.join(path, "foo.xml"),
                    mode="ab",
                    encoding=encoding
                )
            ]
        )

    def test_open_rplus(self):
        path = "/foo/bar"

        base = unittest.mock.Mock()
        base.save_path.return_value = path
        resource = ["foo", "bar"]
        encoding = object()

        with unittest.mock.patch("builtins.open") as open_:
            utils.xdgopen_generic(
                resource,
                "foo.xml",
                "r+b",
                load_paths=base.load_paths,
                save_path=base.save_path,
                encoding=encoding
            )

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.save_path(*resource),
            ]
        )

        self.assertSequenceEqual(
            open_.mock_calls,
            [
                unittest.mock.call(
                    os.path.join(path, "foo.xml"),
                    mode="r+b",
                    encoding=encoding
                )
            ]
        )


class Testxdgconfigopen(unittest.TestCase):
    def test_delegate_to_xdgopen_generic(self):
        mode = "fnord"
        encoding = object()

        with unittest.mock.patch(
                "mlxc.utils.xdgopen_generic"
        ) as xdgopen_generic:
            utils.xdgconfigopen("foo", "bar", "baz.xml",
                                mode=mode,
                                encoding=encoding)

        self.assertSequenceEqual(
            xdgopen_generic.mock_calls,
            [
                unittest.mock.call(
                    ["foo", "bar"],
                    "baz.xml",
                    mode,
                    xdg.BaseDirectory.load_config_paths,
                    xdg.BaseDirectory.save_config_path,
                    encoding=encoding
                )
            ]
        )


class Testxdgdataopen(unittest.TestCase):
    def test_delegate_to_xdgopen_generic(self):
        mode = "fnord"
        encoding = object()

        with unittest.mock.patch(
                "mlxc.utils.xdgopen_generic"
        ) as xdgopen_generic:
            utils.xdgdataopen("foo", "bar", "baz.xml",
                              mode=mode,
                              encoding=encoding)

        self.assertSequenceEqual(
            xdgopen_generic.mock_calls,
            [
                unittest.mock.call(
                    ["foo", "bar"],
                    "baz.xml",
                    mode,
                    xdg.BaseDirectory.load_data_paths,
                    xdg.BaseDirectory.save_data_path,
                    encoding=encoding
                )
            ]
        )
