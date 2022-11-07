import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
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
    hosts = []

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()
        self.service = ConfluentServices.CONTROL_CENTER

    def build_properties(self):

        # Get the hosts for given service
        hosts = self.get_service_host(self.service, self.inventory)
        self.hosts = hosts
        if not hosts:
            logger.error(f"Could not find any host with service {self.service.value.get('name')} ")
            return

        host_service_properties = self.get_property_mappings(self.input_context, self.service, hosts)
        service_properties = host_service_properties.get(hosts[0]).get(DEFAULT_KEY)

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, self.service, hosts)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties
        self.__build_custom_properties(host_service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(hosts)

    def __build_daemon_properties(self, input_context: InputContext, service: ConfluentServices, hosts: list):

        # User group information
        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):
        for key, value in vars(ControlCenterServicePropertyBaseBuilder).items():
            if callable(getattr(ControlCenterServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(ControlCenterServicePropertyBaseBuilder, key)
                logger.info(f"Calling ControlCenter property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, host_service_properties: dict, mapped_properties: set):

        custom_group = "control_center_custom_properties"
        skip_properties = set(FileUtils.get_control_center_configs("skip_properties"))

        _host_service_properties = dict()
        for host in host_service_properties.keys():
            _host_service_properties[host] = host_service_properties.get(host).get(DEFAULT_KEY)
        self.build_custom_properties(inventory=self.inventory, group=self.service.value.get('group'),
                                     custom_properties_group_name=custom_group,
                                     host_service_properties=_host_service_properties, skip_properties=skip_properties,
                                     mapped_properties=mapped_properties)

    def __build_runtime_properties(self, hosts: list):
        data = ('all',
                {'control_center_custom_java_args': self.get_jvm_arguments(self.input_context, self.service, hosts)})
        self.update_inventory(self.inventory, data)

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

        property_list = ["confluent.controlcenter.rest.ssl.truststore.location",
                         "confluent.controlcenter.rest.ssl.truststore.password",
                         "confluent.controlcenter.rest.ssl.keystore.location",
                         "confluent.controlcenter.rest.ssl.keystore.password",
                         "confluent.controlcenter.rest.ssl.key.password"]
        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        property_dict = dict()
        property_dict['ssl_enabled'] = True
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['control_center_truststore_path'] = service_prop.get(
            'confluent.controlcenter.rest.ssl.truststore.location')
        property_dict['ssl_truststore_password'] = service_prop.get(
            'confluent.controlcenter.rest.ssl.truststore.password')
        property_dict['control_center_keystore_path'] = service_prop.get('confluent.controlcenter.rest.ssl.keystore.location')
        property_dict['ssl_keystore_store_password'] = service_prop.get(
            'confluent.controlcenter.rest.ssl.keystore.password')
        property_dict['ssl_keystore_key_password'] = service_prop.get('confluent.controlcenter.rest.ssl.key.password')
        property_dict['ssl_truststore_ca_cert_alias'] = ''

        keystore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                         keystorepass=property_dict['ssl_keystore_store_password'],
                                                         keystorepath=property_dict['control_center_keystore_path'],
                                                         hosts=self.hosts)
        truststore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                           keystorepass=property_dict['ssl_truststore_password'],
                                                           keystorepath=property_dict['control_center_truststore_path'],
                                                           hosts=self.hosts)
        if keystore_aliases:
            # Set the first alias name
            property_dict["ssl_keystore_alias"] = keystore_aliases[0]
        if truststore_aliases:
            property_dict["ssl_truststore_ca_cert_alias"] = truststore_aliases[0]

        return "control_center", property_dict

    def _build_authentication_property(self, service_prop: dict) -> tuple:
        key = 'confluent.controlcenter.rest.authentication.method'
        self.mapped_service_properties.add(key)
        value = service_prop.get(key)
        if value is not None and value == 'BASIC':
            return "all", {'control_center_authentication_type': 'basic'}
        return "all", {}

    def _build_mtls_property(self, service_prop: dict) -> tuple:

        broker_group = ConfluentServices.KAFKA_BROKER.value.get('group')
        if broker_group in self.inventory.groups and \
                'ssl_mutual_auth_enabled' in self.inventory.groups.get(broker_group).vars:
            return "control_center", {'ssl_mutual_auth_enabled': True}
        return 'all', {}

    def _build_rbac_properties(self, service_prop: dict) -> tuple:
        key1 = 'confluent.controlcenter.rest.authentication.method'
        if service_prop.get(key1) is None:
            return 'control_center', {'rbac_enabled': False}
        property_dict = dict()
        key2 = 'public.key.path'
        key3 = 'confluent.metadata.bootstrap.server.urls'
        property_dict['rbac_enabled'] = True
        property_dict['rbac_enabled_public_pem_path'] = service_prop.get(key2)
        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        self.mapped_service_properties.add(key3)
        return 'control_center', property_dict

    def _build_ldap_properties(self, service_prop: dict) -> tuple:
        property_dict = dict()
        key = 'confluent.metadata.basic.auth.user.info'
        self.mapped_service_properties.add(key)
        if service_prop.get(key) is not None:
            metadata_user_info = service_prop.get(key)
            property_dict['control_center_ldap_user'] = metadata_user_info.split(':')[0]
            property_dict['control_center_ldap_password'] = metadata_user_info.split(':')[1]
        return 'all', property_dict


class ControlCenterServicePropertyBaseBuilder60(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBaseBuilder61(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBaseBuilder62(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBaseBuilder70(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBaseBuilder71(ControlCenterServicePropertyBaseBuilder):
    pass


class ControlCenterServicePropertyBaseBuilder72(ControlCenterServicePropertyBaseBuilder):
    pass
