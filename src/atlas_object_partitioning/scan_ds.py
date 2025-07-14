from typing import Optional
from func_adl_servicex_xaodr25 import FuncADLQueryPHYSLITE
from servicex import Sample, ServiceXSpec, dataset, deliver
from servicex_analysis_utils import to_awk


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
            "n_electrons": e.Electrons().Count(),
            "n_muons": e.Muons().Count(),
            # "n_taus": e.TauJets().Count(),
        }
    )

    def _nfiles_value(n_files):
        if n_files == 0:
            return None
        return n_files

    result = to_awk(
        deliver(
            ServiceXSpec(
                Sample=[
                    Sample(
                        Name="object_counts",
                        Dataset=dataset.Rucio(ds_name),
                        NFiles=_nfiles_value(n_files),
                        Query=query,  # type: ignore
                    )
                ]
            ),
            servicex_name=servicex_name,
            ignore_local_cache=ignore_local_cache,
        )
    )
    return result["object_counts"]
