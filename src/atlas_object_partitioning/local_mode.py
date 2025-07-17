import logging
import os
import re
from pathlib import Path
from typing import Optional
from enum import Enum
from servicex import Sample, ServiceXSpec, dataset, deliver as sx_deliver

# ServiceX-Local imports
try:
    from servicex_local import DockerScienceImage, LocalXAODCodegen, SXLocalAdaptor
except ImportError:
    DockerScienceImage = LocalXAODCodegen = SXLocalAdaptor = None


class SXLocationOptions(Enum):
    mustUseLocal = "mustUseLocal"
    mustUseRemote = "mustUseRemote"
    anyLocation = "anyLocation"


def find_dataset(ds_name: str, prefer_local: bool = False):
    """Heuristics to determine dataset type."""
    if re.match(r"^https?://", ds_name):
        url = ds_name
        if not prefer_local:
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            if "cernbox.cern.ch" in parsed_url.netloc and parsed_url.path.startswith(
                "/files/spaces"
            ):
                remote_file = f"root://eospublic.cern.ch{parsed_url.path[13:]}"
                return dataset.FileList([remote_file]), SXLocationOptions.mustUseRemote
        return dataset.FileList([url]), SXLocationOptions.anyLocation
    elif re.match(r"^file://", ds_name):
        from urllib.parse import urlparse, unquote

        parsed_uri = urlparse(ds_name)
        file_path = unquote(parsed_uri.path)
        if os.name == "nt" and file_path.startswith("/"):
            file_path = file_path[1:]
        file = Path(file_path).absolute()
        if file.exists():
            return dataset.FileList([str(file)]), SXLocationOptions.mustUseLocal
        else:
            raise ValueError(f"This local file {file} does not exist.")
    elif re.match(r"^rucio://", ds_name):
        did = ds_name[8:]
        return dataset.Rucio(did), SXLocationOptions.mustUseRemote
    else:
        file = Path(ds_name).absolute()
        if file.exists():
            return dataset.FileList([str(file)]), SXLocationOptions.mustUseLocal
        else:
            if os.path.sep in ds_name:
                raise ValueError(
                    f"{ds_name} looks like a file path, but the file does not exist"
                )
            did = ds_name
            return dataset.Rucio(did), SXLocationOptions.mustUseRemote


def install_sx_local():
    codegen_name = "atlasr22-local"
    if None in (LocalXAODCodegen, DockerScienceImage, SXLocalAdaptor):
        raise ImportError("servicex-local is not installed or could not be imported.")
    codegen = LocalXAODCodegen()  # type: ignore
    science_runner = DockerScienceImage(
        "sslhep/servicex_func_adl_xaod_transformer:25.2.41",
    )  # type: ignore
    adaptor = SXLocalAdaptor(
        codegen, science_runner, codegen_name, "http://localhost:5001"
    )  # type: ignore
    logging.info(f"Using local ServiceX endpoint: codegen {codegen_name}")
    return codegen_name, "local-backend", adaptor


def build_sx_spec(
    query,
    ds_name: str,
    prefer_local: bool = False,
    backend_name: Optional[str] = None,
    n_files: Optional[int] = None,
    title: str = "MySample",
):
    dataset_obj, location_options = find_dataset(ds_name, prefer_local=prefer_local)
    if location_options == SXLocationOptions.mustUseRemote:
        use_local = False
    elif prefer_local or location_options == SXLocationOptions.mustUseLocal:
        use_local = True
    else:
        use_local = False
    adaptor = None
    if use_local:
        codegen_name, backend_name_local, adaptor = install_sx_local()
        backend = backend_name_local
    else:
        backend = backend_name
        codegen_name = "atlasr25"
    spec = ServiceXSpec(
        Sample=[
            Sample(
                Name=title,
                Dataset=dataset_obj,
                Query=query,
                Codegen=codegen_name,
                NFiles=n_files,
            ),
        ],
    )
    return spec, backend, adaptor


def deliver(
    spec,
    servicex_name: Optional[str] = None,
    ignore_local_cache: bool = False,
    run_locally: bool = False,
    adaptor=None,
):
    """Deliver function supporting local mode."""
    if run_locally or (servicex_name == "local-backend"):
        if adaptor is None:
            _, _, adaptor = install_sx_local()
        if SXLocalAdaptor is None:
            raise ImportError(
                "servicex-local is not installed or could not be imported."
            )
        import servicex_local

        return servicex_local.deliver(
            spec, adaptor=adaptor, ignore_local_cache=ignore_local_cache
        )
    else:
        return sx_deliver(
            spec, servicex_name=servicex_name, ignore_local_cache=ignore_local_cache
        )
