from func_adl_servicex_xaodr25 import FuncADLQueryPHYSLITE
from servicex import Sample, ServiceXSpec, dataset, deliver
from servicex_analysis_utils import to_awk


def collect_object_counts(ds_name: str):

    # Build the query to count objects per event
    query = FuncADLQueryPHYSLITE().Select(
        lambda e: {
            "n_jets": e.Jets().Count(),
            "n_electrons": e.Electrons().Count(),
            "n_muons": e.Muons().Count(),
            # "n_taus": e.TauJets().Count(),
        }
    )

    # Run the query on a single file for a fast result (remove NFiles for full sample)
    result = to_awk(
        deliver(
            ServiceXSpec(
                Sample=[
                    Sample(
                        Name="object_counts",
                        Dataset=dataset.Rucio(ds_name),
                        NFiles=1,
                        Query=query,  # type: ignore
                    )
                ]
            ),
        )
    )

    counts = result["object_counts"]
    return counts
