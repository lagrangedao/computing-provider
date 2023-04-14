import datetime
import pytz
import socket
import logging
from kubernetes import client, config


class Container:
    def __init__(self, name, image, container_port, host_port):
        self.name = name
        self.image = image
        self.container_port = container_port
        self.host_port = host_port


def list_all_pods():
    config.load_kube_config()

    v1 = client.CoreV1Api()
    logging.info("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        logging.info("Pod id: %s, namespace: %s, pod name: %s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


def create_deployment_object(container: Container, label: str):
    # Configure Pod template container
    container = client.V1Container(
        name=container.name,
        image=container.image,
        ports=[client.V1ContainerPort(container_port=container.container_port, host_port=container.host_port)],
        # resources=client.V1ResourceRequirements(
        #     requests={"cpu": "100m", "memory": "200Mi"},
        #     limits={"cpu": "500m", "memory": "500Mi"},
        # ),
    )

    # Create and configure a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": label}),
        spec=client.V1PodSpec(containers=[container]),
    )

    # Create the specification of deployment
    spec = client.V1DeploymentSpec(
        replicas=1, template=template, selector={
            "matchLabels":
                {"app": label}})

    # Instantiate the deployment object
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=label),
        spec=spec,
    )

    return deployment


def update_deployment(api, deployment, image: str, name: str):
    # Update container image
    deployment.spec.template.spec.containers[0].image = image

    # patch the deployment
    resp = api.patch_namespaced_deployment(
        name=name, namespace="default", body=deployment
    )
    logging.info("Deployment's container image updated. Deployment name: %s" % resp.metadata.name)


def restart_deployment(api, deployment, name: str):
    # update `spec.template.metadata` section
    # to add `kubectl.kubernetes.io/restartedAt` annotation
    deployment.spec.template.metadata.annotations = {
        "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow()
        .replace(tzinfo=pytz.UTC)
        .isoformat()
    }

    # patch the deployment
    resp = api.patch_namespaced_deployment(
        name=name, namespace="default", body=deployment
    )
    logging.info("Deployment restarted. Deployment name: %s" % resp.metadata.name)


def create_service(api, port, label: str):
    body = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(
            name=label
        ),
        spec=client.V1ServiceSpec(
            selector={"app": label},
            ports=[client.V1ServicePort(
                port=port
            )]
        )
    )
    # Creation of the Deployment in specified namespace
    # (Can replace "default" with a namespace you may have created)
    resp = api.create_namespaced_service(namespace="default", body=body)
    logging.info("Service created")


def create_ingress(api, port, label: str, host_name: str):
    body = client.V1Ingress(
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata=client.V1ObjectMeta(name=label, annotations={
            "kubernetes.io/ingress.class": "traefik"
        }),
        spec=client.V1IngressSpec(
            rules=[client.V1IngressRule(
                host=host_name,
                http=client.V1HTTPIngressRuleValue(
                    paths=[client.V1HTTPIngressPath(
                        path="/",
                        path_type="Exact",
                        backend=client.V1IngressBackend(
                            service=client.V1IngressServiceBackend(
                                port=client.V1ServiceBackendPort(
                                    number=port,
                                ),
                                name=label)
                        )
                    )]
                )
            )
            ]
        )
    )
    # Creation of the Deployment in specified namespace
    # (Can replace "default" with a namespace you may have created)
    resp = api.create_namespaced_ingress(
        namespace="default",
        body=body
    )
    logging.info("Ingress created")


def create_deployment(api, deployment):
    # Create deployment
    resp = api.create_namespaced_deployment(
        body=deployment, namespace="default"
    )
    logging.info("Deployment created. Deployment name: %s" % resp.metadata.name)



def delete_service(api, service_name: str):
    # Delete service
    resp = api.delete_namespaced_service(
        name=service_name,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )
    logging.info("Service deleted")


def delete_ingress(api, ingress_name: str):
    # Delete ingress
    resp = api.delete_namespaced_ingress(
        name=ingress_name,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )
    logging.info("Ingress deleted")


def delete_deployment(api, deployment_name: str):
    # Delete deployment
    resp = api.delete_namespaced_deployment(
        name=deployment_name,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )
    logging.info("Deployment deleted")


def get_random_port():
    sock = socket.socket()
    sock.bind(('', 0))
    return sock.getsockname()[1]