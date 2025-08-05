from typing import Optional

from func_adl_servicex_xaodr25 import FuncADLQueryPHYSLITE
from servicex_analysis_utils import to_awk

from atlas_object_partitioning.local_mode import build_sx_spec
from atlas_object_partitioning.local_mode import deliver


def collect_object_counts(
    ds_name: str,
    n_files: int = 1,
    servicex_name: Optional[str] = None,
    ignore_local_cache: bool = False,
):

    # Build the query to count objects per event
    query = FuncADLQueryPHYSLITE().Select(
        lambda e: {
            "n_jets": e.Jets().Count(),
            "n_large_jets": e.Jets("AnalysisLargeRJets").Count(),
            "n_electrons": e.Electrons().Count(),
            "n_muons": e.Muons().Count(),
            "n_taus": e.TauJets("AnalysisTauJets").Count(),
            "n_photons": e.Photons().Count(),
            "met": e.MissingET().First().met() / 1000.0,
        }
    )

    def _nfiles_value(n_files):
        if n_files == 0:
            return None
        return n_files

    # Next, deliver the data
    spec, backend_name, adaptor = build_sx_spec(
        query,
        ds_name,
        backend_name=servicex_name,
        n_files=_nfiles_value(n_files),
        title="object_counts",
    )
    r = deliver(
        spec, backend_name, adaptor=adaptor, ignore_local_cache=ignore_local_cache
    )

    result = to_awk(r)

    return result["object_counts"]
