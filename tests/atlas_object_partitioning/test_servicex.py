import importlib
import os
import sys
import types
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))


def _create_servicex_stub():
    sx = types.ModuleType("servicex")

    class Dummy:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class dataset(types.SimpleNamespace):
        class FileList(Dummy):
            pass

        class Rucio(Dummy):
            pass

    sx.Sample = Dummy
    sx.ServiceXSpec = Dummy
    sx.dataset = dataset

    def deliver(spec, servicex_name=None, ignore_local_cache=False):
        return {
            "called": "servicex",
            "spec": spec,
            "servicex_name": servicex_name,
            "ignore_local_cache": ignore_local_cache,
        }

    sx.deliver = deliver
    return sx


def _create_servicex_local_stub():
    sxl = types.ModuleType("servicex_local")

    class Dummy:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    sxl.DockerScienceImage = Dummy
    sxl.LocalXAODCodegen = Dummy
    sxl.SXLocalAdaptor = Dummy

    def deliver(spec, adaptor=None, ignore_local_cache=False):
        return {
            "called": "servicex_local",
            "spec": spec,
            "adaptor": adaptor,
            "ignore_local_cache": ignore_local_cache,
        }

    sxl.deliver = deliver
    return sxl


def _create_func_adl_stub():
    fadl = types.ModuleType("func_adl_servicex_xaodr25")

    class Query:
        def Select(self, _):
            return "query"

    fadl.FuncADLQueryPHYSLITE = Query
    return fadl


def _create_analysis_utils_stub():
    sau = types.ModuleType("servicex_analysis_utils")

    def to_awk(result):
        return {"object_counts": result}

    sau.to_awk = to_awk
    return sau



def test_collect_object_counts_remote(monkeypatch):
    """Ensure remote ServiceX call path is used."""
    sx = _create_servicex_stub()
    fadl = _create_func_adl_stub()
    sau = _create_analysis_utils_stub()
    monkeypatch.setitem(sys.modules, "servicex", sx)
    monkeypatch.setitem(sys.modules, "func_adl_servicex_xaodr25", fadl)
    monkeypatch.setitem(sys.modules, "servicex_analysis_utils", sau)

    import atlas_object_partitioning.scan_ds as scan_ds
    import atlas_object_partitioning.local_mode as local_mode
    importlib.reload(local_mode)
    importlib.reload(scan_ds)

    called = {}

    def fake_deliver(spec, servicex_name=None, ignore_local_cache=False):
        called["spec"] = spec
        called["servicex_name"] = servicex_name
        called["ignore_local_cache"] = ignore_local_cache
        return "result"

    monkeypatch.setattr(local_mode, "sx_deliver", fake_deliver)

    result = scan_ds.collect_object_counts(
        "rucio://DUMMY", n_files=1, servicex_name="my-sx", ignore_local_cache=True
    )

    assert result == "result"
    assert called["servicex_name"] == "my-sx"
    assert called["ignore_local_cache"] is True


def test_collect_object_counts_local(monkeypatch):
    """Ensure local ServiceX call path is used."""
    sx = _create_servicex_stub()
    sxl = _create_servicex_local_stub()
    fadl = _create_func_adl_stub()
    sau = _create_analysis_utils_stub()
    monkeypatch.setitem(sys.modules, "servicex", sx)
    monkeypatch.setitem(sys.modules, "servicex_local", sxl)
    monkeypatch.setitem(sys.modules, "func_adl_servicex_xaodr25", fadl)
    monkeypatch.setitem(sys.modules, "servicex_analysis_utils", sau)

    import atlas_object_partitioning.scan_ds as scan_ds
    import atlas_object_partitioning.local_mode as local_mode
    importlib.reload(local_mode)
    importlib.reload(scan_ds)

    monkeypatch.setattr(local_mode, "SXLocalAdaptor", object())

    def fake_install():
        return "cg", "local-backend", "adaptor"

    monkeypatch.setattr(local_mode, "install_sx_local", fake_install)

    called = {}

    def fake_local_deliver(spec, adaptor=None, ignore_local_cache=False):
        called["spec"] = spec
        called["adaptor"] = adaptor
        called["ignore_local_cache"] = ignore_local_cache
        return "local_result"

    monkeypatch.setattr(sxl, "deliver", fake_local_deliver)

    with tempfile.NamedTemporaryFile() as tmp:
        result = scan_ds.collect_object_counts(tmp.name, n_files=1, ignore_local_cache=False)

    assert result == "local_result"
    assert called["adaptor"] == "adaptor"
    assert called["ignore_local_cache"] is False
