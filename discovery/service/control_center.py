import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class ControlCenterServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="ControlCenterServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class ControlCenterServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        # Get the hosts for given service
        service = ConfluentServices.CONTROL_CENTER
        hosts = self.get_service_host(service, self.inventory)
        if not hosts:
            logger.error(f"Could not find any host with service {service.value.get('name')} ")

        host_service_properties = self.get_property_mappings(self.input_context, service, hosts)
        service_properties = host_service_properties.get(hosts[0])

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, service, hosts)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties
        self.__build_custom_properties(service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(service_properties)

    def __build_daemon_properties(self, input_context: InputContext, service: ConfluentServices, hosts: list):

        # User group information
        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):
        for key, value in vars(ControlCenterServicePropertyBaseBuilder).items():
            if callable(getattr(ControlCenterServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(ControlCenterServicePropertyBaseBuilder, key)
                logger.debug(f"Calling ControlCenter property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):

        group = "control_center_custom_properties"
        skip_properties = set(FileUtils.get_control_center_configs("skip_properties"))
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)

    def __build_runtime_properties(self, service_properties: dict):
        pass

    def _build_service_protocol_port(self, service_prop: dict) -> tuple:
        key = "confluent.controlcenter.rest.listeners"
        self.mapped_service_properties.add(key)
        from urllib.parse import urlparse
        parsed_uri = urlparse(service_prop.get(key))
        return "all", {
            "control_center_http_protocol": parsed_uri.scheme,
            "control_center_listener_hostname": parsed_uri.hostname,
            "control_center_port": parsed_uri.port
        }

    def _build_control_center_internal_replication_property(self, service_prop: dict) -> tuple:
        key1 = "confluent.controlcenter.command.topic.replication"
        key2 = "confluent.controlcenter.internal.topics.replication"
        key3 = "confluent.metrics.topic.replication"
        key4 = "confluent.monitoring.interceptor.topic.replication"
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        self.mapped_service_properties.add(key3)
        self.mapped_service_properties.add(key4)
        return "all", {"control_center_default_internal_replication_factor": int(service_prop.get(key1))}

    def _build_tls_properties(self, service_prop: dict) -> tuple:
        key = "confluent.controlcenter.rest.listeners"
        control_center_listener = service_prop.get(key)

        if control_center_listener.find('https') < 0:
            return "all", {}

        property_list = ["confluent.controlcenter.rest.ssl.truststore.location", "confluent.controlcenter.rest.ssl.truststore.password", "confluent.controlcenter.rest.ssl.keystore.location",
                            "confluent.controlcenter.rest.ssl.keystore.password", "confluent.controlcenter.rest.ssl.key.password"]
        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        property_dict = dict()
        property_dict['ssl_enabled'] = True
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['ssl_truststore_filepath'] = service_prop.get('confluent.controlcenter.rest.ssl.truststore.location')
        property_dict['ssl_truststore_password'] = service_prop.get('confluent.controlcenter.rest.ssl.truststore.password')
        property_dict['ssl_keystore_filepath'] = service_prop.get('confluent.controlcenter.rest.ssl.keystore.location')
        property_dict['ssl_keystore_store_password'] = service_prop.get('confluent.controlcenter.rest.ssl.keystore.password')
        property_dict['ssl_keystore_key_password'] = service_prop.get('confluent.controlcenter.rest.ssl.key.password')

        return "control_center", property_dict


class ControlCenterServicePropertyBuilder60(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBuilder61(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBuilder62(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBuilder70(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBuilder71(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBuilder72(ControlCenterServicePropertyBaseBuilder):
    pass
