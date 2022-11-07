import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class ZookeeperServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="ZookeeperServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class ZookeeperServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None
    hosts = []

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()
        self.service = ConfluentServices.ZOOKEEPER

    def build_properties(self):

        # Get the hosts for given service
        hosts = self.get_service_host(self.service, self.inventory)
        self.hosts = hosts

        if not hosts:
            logger.error(f"Could not find any host with service {self.service.value.get('name')} ")

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

        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):

        for key, value in vars(ZookeeperServicePropertyBaseBuilder).items():
            if callable(getattr(ZookeeperServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(ZookeeperServicePropertyBaseBuilder, key)
                logger.info(f"Calling Zookeeper property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, host_service_properties: dict, mapped_properties: set):

        custom_group = "zookeeper_custom_properties"
        skip_properties = set(FileUtils.get_zookeeper_configs("skip_properties"))
<<<<<<< HEAD
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)
=======

        # Get host server properties dictionary
        _host_service_properties = dict()
        for host in host_service_properties.keys():
            _host_service_properties[host] = host_service_properties.get(host).get(DEFAULT_KEY)
        self.build_custom_properties(inventory=self.inventory, group=self.service.value.get('group'),
                                     custom_properties_group_name=custom_group,
                                     host_service_properties=_host_service_properties, skip_properties=skip_properties,
                                     mapped_properties=mapped_properties)
>>>>>>> 5378ad6d (Add secret protection support and enahanced customer properties)

    def __build_runtime_properties(self, hosts: list):
        # Build Java runtime overrides
        data = ('all', {'zookeeper_custom_java_args': self.get_jvm_arguments(self.input_context, self.service, hosts)})
        self.update_inventory(self.inventory, data)

    def __get_user_dict(self, service_prop: dict, key: str) -> dict:
        pass

    def _build_service_port_properties(self, service_prop: dict) -> tuple:
        key = "clientPort"
        self.mapped_service_properties.add(key)
        if service_prop.get(key) is not None:
            return 'all', {"zookeeper_client_port": int(service_prop.get(key))}
        return 'all', {}

    def _build_ssl_properties(self, service_properties: dict) -> tuple:

        property_dict = dict()
        property_list = ["secureClientPort", "ssl.keyStore.location", "ssl.keyStore.password",
                         "ssl.trustStore.location", "ssl.trustStore.password"]

        for property_key in property_list:
            self.mapped_service_properties.add(property_key)

        zookeeper_ssl_enabled = bool(service_properties.get('secureClientPort', False))

        if zookeeper_ssl_enabled == False:
            return "all", {}

        property_dict['ssl_enabled'] = True
        property_dict['zookeeper_keystore_path'] = service_properties.get('ssl.keyStore.location')
        property_dict['ssl_keystore_store_password'] = service_properties.get('ssl.keyStore.password')
        property_dict['zookeeper_truststore_path'] = service_properties.get('ssl.trustStore.location')
        property_dict['ssl_truststore_password'] = service_properties.get('ssl.trustStore.password')
        property_dict['ssl_provided_keystore_and_truststore'] = True
        property_dict['ssl_provided_keystore_and_truststore_remote_src'] = True
        property_dict['ssl_truststore_ca_cert_alias'] = ''

        keystore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                         keystorepass=property_dict['ssl_keystore_store_password'],
                                                         keystorepath=property_dict['zookeeper_keystore_path'],
                                                         hosts=self.hosts)
        truststore_aliases = self.get_keystore_alias_names(input_context=self.input_context,
                                                           keystorepass=property_dict['ssl_truststore_password'],
                                                           keystorepath=property_dict['zookeeper_truststore_path'],
                                                           hosts=self.hosts)
        if keystore_aliases:
            # Set the first alias name
            property_dict["ssl_keystore_alias"] = keystore_aliases[0]
        if truststore_aliases:
            property_dict["ssl_truststore_ca_cert_alias"] = truststore_aliases[0]

        return "zookeeper", property_dict

    def _build_mtls_properties(self, service_properties: dict) -> tuple:
        zookeeper_client_authentication_type = service_properties.get('ssl.clientAuth')
        if zookeeper_client_authentication_type == 'need':
            return "zookeeper", {'ssl_mutual_auth_enabled': True}

        return "all", {}


class ZookeeperServicePropertyBaseBuilder60(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder61(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder62(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder70(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder71(ZookeeperServicePropertyBaseBuilder):
    pass


class ZookeeperServicePropertyBaseBuilder72(ZookeeperServicePropertyBaseBuilder):
    pass
