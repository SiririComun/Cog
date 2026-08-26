import json
import re


class BlockDesignPruner:
    """Prunes noisy default Vivado Zynq PS7/MIO boilerplate from .bd files (saving ~80% tokens)."""

    # Noise parameter prefixes to strip from Processing System blocks
    PS_NOISE_PREFIXES = (
        "PCW_MIO_", "PCW_NOR_", "PCW_NAND_", "PCW_SMC_", "PCW_DDR_",
        "PCW_PACKAGE_DDR_", "PCW_UIPARAM_DDR_CLOCK_", "PCW_UIPARAM_DDR_DQS_",
        "PCW_UIPARAM_DDR_DQ_", "PCW_ACT_"
    )

    @classmethod
    def prune_bd_json(cls, raw_content: str) -> str:
        try:
            data = json.loads(raw_content)
        except Exception:
            return raw_content  # Fallback if invalid JSON

        design = data.get("design", {})

        # 1. Prune components
        components = design.get("components", {})
        for comp_name, comp_data in components.items():
            if not isinstance(comp_data, dict):
                continue
            
            # Prune verbose processing_system7 default settings
            vlnv = comp_data.get("vlnv", "")
            if "processing_system7" in vlnv:
                params = comp_data.get("parameters", {})
                pruned_params = {
                    k: v for k, v in params.items()
                    if not k.startswith(cls.PS_NOISE_PREFIXES)
                }
                comp_data["parameters"] = pruned_params
                
                # Prune long default memory map segments list if present
                if "addressing" in comp_data:
                    comp_data["addressing"] = "<Default Zynq Memory Map Pruned>"

        # Re-encode as formatted compact JSON
        return json.dumps(data, indent=2)