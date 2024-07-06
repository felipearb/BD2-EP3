from flask import Flask, render_template, request
import psycopg2
from configparser import ConfigParser

app = Flask(__name__)

def get_db_connection():
    config = ConfigParser()
    config.read('config.ini')

    dbname = config.get('database', 'dbname')
    user = config.get('database', 'user')
    password = config.get('database', 'password')
    host = config.get('database', 'host')

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host
    )
    return conn

def init_db():
    create_tables_sql = """
    CREATE SCHEMA IF NOT EXISTS mydb;

    CREATE TABLE IF NOT EXISTS medico (
        crm VARCHAR(10) NOT NULL,
        nomeM VARCHAR(45) NOT NULL,
        telefoneM VARCHAR(11) NOT NULL,
        percentual DECIMAL(4,2) NOT NULL,
        PRIMARY KEY (crm)
    );

    CREATE TABLE IF NOT EXISTS agenda (
        idAgenda SERIAL PRIMARY KEY,
        diaSemana VARCHAR(7) NOT NULL,
        horaInicio TIME NOT NULL,
        horaFim TIME NOT NULL,
        crm VARCHAR(10) NOT NULL,
        CONSTRAINT fk_medico_agenda_crm
            FOREIGN KEY (crm)
            REFERENCES medico (crm)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS especialidade (
        idEsp SERIAL PRIMARY KEY,
        nomeE VARCHAR(45) NOT NULL,
        indice INT NOT NULL,
        UNIQUE (nomeE)
    );

    CREATE TABLE IF NOT EXISTS exerceEsp (
        crm VARCHAR(10) NOT NULL,
        idEsp INT NOT NULL,
        CONSTRAINT fk_medico_exerceEsp_crm
            FOREIGN KEY (crm)
            REFERENCES medico (crm)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT fk_especialidade_exerceEsp_idEsp
            FOREIGN KEY (idEsp)
            REFERENCES especialidade (idEsp)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

    CREATE TABLE IF NOT EXISTS paciente (
        idPac SERIAL PRIMARY KEY,
        cpf VARCHAR(11) NOT NULL,
        nomeP VARCHAR(45) NOT NULL,
        telefonePac VARCHAR(11),
        endereco VARCHAR(120),
        idade INT NOT NULL,
        sexo CHAR(1) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS consulta (
        idCon SERIAL PRIMARY KEY,
        crm VARCHAR(10) NOT NULL,
        idEsp INT NOT NULL,
        idPac INT NOT NULL,
        data DATE NOT NULL,
        horaInicCon TIME,
        horaFimCon TIME,
        pagou CHAR(1) NOT NULL,
        valorPago DECIMAL(10,2),
        formaPagamento VARCHAR(15),
        CONSTRAINT fk_medico_consulta_crm
            FOREIGN KEY (crm)
            REFERENCES medico (crm)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        CONSTRAINT fk_especialidade_consulta_idEsp
            FOREIGN KEY (idEsp)
            REFERENCES especialidade (idEsp)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT fk_paciente_consulta_idPac
            FOREIGN KEY (idPac)
            REFERENCES paciente (idPac)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

    CREATE TABLE IF NOT EXISTS diagnostico (
        idDiagnostico SERIAL PRIMARY KEY,
        tratamentoRecomendado VARCHAR(50) NOT NULL,
        remediosReceitados VARCHAR(250),
        observacoes VARCHAR(250),
        idCon INT NOT NULL,
        CONSTRAINT fk_consulta_diagnostico_idCon
            FOREIGN KEY (idCon)
            REFERENCES consulta (idCon)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

    CREATE TABLE IF NOT EXISTS doenca (
        idDoenca SERIAL PRIMARY KEY,
        nomeD VARCHAR(50) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS diagnostica (
        idDiagnostico INT NOT NULL,
        idDoenca INT NOT NULL,
        CONSTRAINT fk_diagnostico_diagnostica_idDiagnostico
            FOREIGN KEY (idDiagnostico)
            REFERENCES diagnostico (idDiagnostico)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT fk_doenca_diagnostica_idDoenca
            FOREIGN KEY (idDoenca)
            REFERENCES doenca (idDoenca)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(create_tables_sql)
    conn.commit()
    cur.close()
    conn.close()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form['search_query']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medico")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
