from influxdb_client import InfluxDBClient, Point, WriteOptions

INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "SEU_TOKEN_AQUI"
INFLUX_ORG = "SEU_ORG"
INFLUX_BUCKET = "obd_data"


client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = client.write_api(write_options=WriteOptions(batch_size=1))


def enviar_inspecao(usuario, veiculo, farois, lanternas, pneus):
    point = (
        Point("inspecao")
        .tag("usuario", usuario)
        .tag("veiculo", veiculo)
        .field("farois", 1 if farois == "OK" else 0)
        .field("lanternas", 1 if lanternas == "OK" else 0)
        .field("pneus", 1 if pneus == "OK" else 0)
    )

    write_api.write(bucket=INFLUX_BUCKET, record=point)


def enviar_finalizacao(usuario, veiculo, km_rodado):
    point = (
        Point("turno")
        .tag("usuario", usuario)
        .tag("veiculo", veiculo)
        .field("km_rodado", km_rodado)
    )

    write_api.write(bucket=INFLUX_BUCKET, record=point)