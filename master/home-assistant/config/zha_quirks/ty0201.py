"""Tuya TY0201 temperature, humidity and optional illumination sensors."""

from zigpy.profiles import zha
from zigpy.profiles.zha import DeviceType
from zigpy.quirks import CustomCluster, CustomDevice
import zigpy.types as t
from zigpy.zcl.clusters.general import Basic, Identify, Ota, PowerConfiguration, Time
from zigpy.zcl.clusters.measurement import (
    IlluminanceMeasurement,
    RelativeHumidity,
    TemperatureMeasurement,
)
from zigpy.zdo.types import NodeDescriptor

from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    NODE_DESCRIPTOR,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)

class TemperatureHumidtySensorWithScreen(CustomDevice):
    """Temu temperature and humidity sensor with screen."""

    signature = {
        #  <SimpleDescriptor endpoint=1, profile=260, device_type="0x0302"
        #  input_clusters=["0x0000", "0x0001", "0x0003", "0x0402", "0x0405"]
        #  output_clusters=["0x0019"]>
        MODELS_INFO: [("_TZ3000_bjawzodf", "TY0201")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: DeviceType.TEMPERATURE_SENSOR,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    TemperatureMeasurement.cluster_id,
                    RelativeHumidity.cluster_id,
                  ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    TemperatureMeasurement.cluster_id,
                    RelativeHumidity.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                ],
            },
        },
    }