from influxdb_client import InfluxDBClient, Point, WriteOptions

# Configuracoes de conexao com o InfluxDB Cloud.
# Troque os placeholders abaixo pelos dados reais do seu bucket.
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "SEU_TOKEN_AQUI"
INFLUX_ORG = "SEU_ORG"
INFLUX_BUCKET = "obd_data"

# Cliente compartilhado para reutilizar a conexao com o InfluxDB.
client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

# batch_size=1 envia cada registro imediatamente, o que facilita acompanhar testes.
write_api = client.write_api(write_options=WriteOptions(batch_size=1))


def enviar_inspecao(usuario, veiculo, farois, lanternas, pneus):
    # Cada item da inspecao vira um campo numerico para facilitar graficos.
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
    # Registra o total rodado no turno finalizado.
    point = (
        Point("turno")
        .tag("usuario", usuario)
        .tag("veiculo", veiculo)
        .field("km_rodado", km_rodado)
    )

    write_api.write(bucket=INFLUX_BUCKET, record=point)
