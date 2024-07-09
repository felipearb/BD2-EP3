from flask import Flask, render_template, request
import psycopg2
from configparser import ConfigParser
import time

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

def init_tables():
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

def init_values():
    conn = get_db_connection()
    cur = conn.cursor()

    # Exemplo para inserir médicos apenas se não existirem
    insert_medico_sql = """
    INSERT INTO medico (crm, nomeM, telefoneM, percentual)
    SELECT * FROM (VALUES
        ('CRM001', 'Dr. João Silva', '12345678901', 10.00),
        ('CRM002', 'Dra. Maria Oliveira', '12345678902', 12.50),
        ('CRM003', 'Dr. Pedro Santos', '12345678903', 15.00),
        ('CRM004', 'Dra. Ana Lima', '12345678904', 8.75),
        ('CRM005', 'Dr. Lucas Costa', '12345678905', 11.00),
        ('CRM006', 'Dra. Fernanda Souza', '12345678906', 14.25),
        ('CRM007', 'Dr. Marcos Ribeiro', '12345678907', 9.50),
        ('CRM008', 'Dra. Carla Almeida', '12345678908', 13.75),
        ('CRM009', 'Dr. Paulo Mendes', '12345678909', 10.50),
        ('CRM010', 'Dra. Laura Azevedo', '12345678910', 16.00)
    ) AS data(crm, nomeM, telefoneM, percentual)
    WHERE NOT EXISTS (
        SELECT 1 FROM medico WHERE medico.crm = data.crm
    );
    """
    
    # Exemplo para inserir registros na tabela agenda
    insert_agenda_sql = """
    INSERT INTO agenda (diaSemana, horaInicio, horaFim, crm)
    SELECT diaSemana, CAST(horaInicio AS TIME), CAST(horaFim AS TIME), crm FROM (
        VALUES
        ('Segunda', '08:00', '12:00', 'CRM001'),
        ('Terça', '09:00', '13:00', 'CRM002'),
        ('Quarta', '10:00', '14:00', 'CRM003'),
        ('Quinta', '11:00', '15:00', 'CRM004'),
        ('Sexta', '12:00', '16:00', 'CRM005'),
        ('Sábado', '13:00', '17:00', 'CRM006'),
        ('Domingo', '14:00', '18:00', 'CRM007'),
        ('Segunda', '08:30', '12:30', 'CRM008'),
        ('Terça', '09:30', '13:30', 'CRM009'),
        ('Quarta', '10:30', '14:30', 'CRM010')
    ) AS data(diaSemana, horaInicio, horaFim, crm)
    WHERE NOT EXISTS (
        SELECT 1 FROM agenda WHERE agenda.crm = data.crm
    );
    """
    
    # Exemplo para inserir registros na tabela especialidade
    insert_especialidade_sql = """
    INSERT INTO especialidade (nomeE, indice)
    SELECT * FROM (VALUES
        ('Cardiologia', 1),
        ('Pediatria', 2),
        ('Ortopedia', 3),
        ('Dermatologia', 4),
        ('Oftalmologia', 5),
        ('Psiquiatria', 6),
        ('Ginecologia', 7),
        ('Urologia', 8),
        ('Endocrinologia', 9),
        ('Oncologia', 10)
    ) AS data(nomeE, indice)
    WHERE NOT EXISTS (
        SELECT 1 FROM especialidade WHERE especialidade.nomeE = data.nomeE
    );
    """
    
    # Exemplo para inserir registros na tabela exerceEsp (relacionamento entre médico e especialidade)
    insert_exerceEsp_sql = """
    INSERT INTO exerceEsp (crm, idEsp)
    SELECT * FROM (VALUES
        ('CRM001', 1),
        ('CRM002', 2),
        ('CRM003', 3),
        ('CRM004', 4),
        ('CRM005', 5),
        ('CRM006', 6),
        ('CRM007', 7),
        ('CRM008', 8),
        ('CRM009', 9),
        ('CRM010', 10)
    ) AS data(crm, idEsp)
    WHERE NOT EXISTS (
        SELECT 1 FROM exerceEsp WHERE exerceEsp.crm = data.crm AND exerceEsp.idEsp = data.idEsp
    );
    """
    
    # Exemplo para inserir pacientes apenas se não existirem
    insert_paciente_sql = """
    INSERT INTO paciente (cpf, nomeP, telefonePac, endereco, idade, sexo)
    SELECT * FROM (VALUES
        ('CPF001', 'José da Silva', '21987654321', 'Rua A, 123', 40, 'M'),
        ('CPF002', 'Maria Oliveira', '11976543210', 'Rua B, 456', 35, 'F'),
        ('CPF003', 'Carlos Souza', '31965478901', 'Av. C, 789', 25, 'M'),
        ('CPF004', 'Ana Lima', '41987654321', 'Rua D, 321', 30, 'F'),
        ('CPF005', 'Paulo Mendes', '11965437890', 'Av. E, 654', 50, 'M'),
        ('CPF006', 'Fernanda Santos', '21987654321', 'Rua F, 987', 45, 'F'),
        ('CPF007', 'Pedro Ribeiro', '11987654321', 'Av. G, 123', 32, 'M'),
        ('CPF008', 'Márcia Almeida', '21965437890', 'Rua H, 456', 28, 'F'),
        ('CPF009', 'Luiza Costa', '11987654321', 'Av. I, 789', 55, 'F'),
        ('CPF010', 'Rafaela Azevedo', '31965437890', 'Rua J, 987', 42, 'F')
    ) AS data(cpf, nomeP, telefonePac, endereco, idade, sexo)
    WHERE NOT EXISTS (
        SELECT 1 FROM paciente WHERE paciente.cpf = data.cpf
    );
    """
    
    # Exemplo para inserir consultas apenas se não existirem
    insert_consulta_sql = """
    INSERT INTO consulta (crm, idEsp, idPac, data, horaInicCon, horaFimCon, pagou, valorPago, formaPagamento)
    SELECT crm, idEsp, idPac, CAST(data AS DATE), CAST(horaInicCon AS TIME), CAST(horaFimCon AS TIME), pagou, valorPago, formaPagamento FROM (
        VALUES
        ('CRM001', 1, 1, '2024-07-10', '08:00', '09:00', 'S', 150.00, 'Dinheiro'),
        ('CRM002', 2, 2, '2024-07-12', '09:00', '10:00', 'S', 200.00, 'Cartão'),
        ('CRM003', 3, 3, '2024-07-15', '10:00', '11:00', 'S', 180.00, 'Dinheiro'),
        ('CRM004', 4, 4, '2024-07-18', '11:00', '12:00', 'N', NULL, NULL),
        ('CRM005', 5, 5, '2024-07-20', '12:00', '13:00', 'S', 190.00, 'Cartão'),
        ('CRM006', 6, 6, '2024-07-22', '13:00', '14:00', 'S', 160.00, 'Dinheiro'),
        ('CRM007', 7, 7, '2024-07-25', '14:00', '15:00', 'N', NULL, NULL),
        ('CRM008', 8, 8, '2024-07-28', '15:00', '16:00', 'S', 220.00, 'Cartão'),
        ('CRM009', 9, 9, '2024-07-30', '16:00', '17:00', 'S', 195.00, 'Dinheiro'),
        ('CRM010', 10, 10, '2024-08-02', '17:00', '18:00', 'S', 180.00, 'Cartão')
    ) AS data(crm, idEsp, idPac, data, horaInicCon, horaFimCon, pagou, valorPago, formaPagamento)
    WHERE NOT EXISTS (
        SELECT 1 FROM consulta WHERE consulta.crm = data.crm AND consulta.idEsp = data.idEsp AND consulta.idPac = data.idPac AND consulta.data = CAST(data.data AS DATE)
    );
    """
    
    # Executa os comandos SQL
    cur.execute(insert_medico_sql)
    cur.execute(insert_agenda_sql)
    cur.execute(insert_especialidade_sql)
    cur.execute(insert_exerceEsp_sql)
    cur.execute(insert_paciente_sql)
    cur.execute(insert_consulta_sql)
    
    # Commit para efetivar as transações no banco de dados
    conn.commit()
    
    # Fecha o cursor e a conexão com o banco de dados
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
    cur.execute("""
        SELECT * FROM medico
        WHERE nomeM ILIKE %s
    """, ('%' + search_query + '%',))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, columns=["crm", "nomeM", "telefoneM", "percentual"])


@app.route('/searchall', methods=['POST'])
def searchall():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medico")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results,columns=["crm", "nomeM", "telefoneM", "percentual"])


@app.route('/list_consultas_paciente_medico', methods=['POST'])
def list_consultas_paciente_medico():
    crm = request.form['crm']
    idPac = request.form['idPac']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT crm, idPac, idEsp, data, horaInicCon
        FROM consulta
        WHERE crm = %s AND idPac = %s
    """, (crm, idPac))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, columns=["crm", "idPac", "idEsp", "data", "horaInicCon"])


@app.route('/list_medicos_uma_especialidade', methods=['POST'])
def list_medicos_uma_especialidade():
    especialidade = request.form['especialidade']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.crm, m.nomeM
        FROM medico m
        JOIN exerceEsp e ON m.crm = e.crm
        JOIN especialidade esp ON e.idEsp = esp.idEsp
        WHERE esp.nomeE = %s
    """, (especialidade,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, columns=["crm","nome"])


@app.route('/list_pacientes_medico_especialidade', methods=['POST'])
def list_pacientes_medico_especialidade():
    medico = request.form['medico']
    especialidade = request.form['especialidade']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.cpf, p.nomeP
        FROM consulta c
        JOIN paciente p ON c.idPac = p.idPac
        JOIN medico m ON c.crm = m.crm
        JOIN especialidade e ON c.idEsp = e.idEsp
        WHERE m.nomeM = %s AND e.nomeE = %s
    """, (medico, especialidade))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, columns=["cpf","nome"])


@app.route('/list_consultas_janeiro', methods=['POST'])
def list_consultas_janeiro():
    mes = request.form['mes']
    ano = request.form['ano']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT crm, idPac, idEsp, data, horaInicCon
        FROM consulta
        WHERE EXTRACT(MONTH FROM data) = %s AND EXTRACT(YEAR FROM data) = %s
    """, (mes, ano))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, columns=["crm","idPaciente","idEspecialiazação","data","horario inicio"])


@app.route('/total_consultas_medico', methods=['POST'])
def total_consultas_medico():
    nomeM = request.form['nomeM']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.idEsp, COUNT(c.idCon) AS TotalConsultas
        FROM consulta c
        JOIN medico m ON c.crm = m.crm
        WHERE m.nomeM = %s
        GROUP BY c.idEsp
    """, (nomeM,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, columns=["id_especialização","quantidade"])


@app.route('/medico_menos_consultas', methods=['GET'])
def medico_menos_consultas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.crm AS CRM, m.nomeM AS NomeM, COUNT(c.idCon) AS TotalConsultas
        FROM medico m
        LEFT JOIN consulta c ON m.crm = c.crm
        GROUP BY m.crm, m.nomeM
        ORDER BY TotalConsultas
        LIMIT 1
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results, columns=["crm","nome", "TotalConsultas"])


@app.route('/remover_consultas_nao_pagas', methods=['POST'])
def remover_consultas_nao_pagas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM consulta
        WHERE pagou = 'N'
    """)
    conn.commit()
    cur.close()
    conn.close()
    
    # Recuperando consultas removidas
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS consultas_removidas
        FROM consulta
        WHERE pagou = 'N'
    """)
    results_remove = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('index.html', results_remove=results_remove)


@app.route('/transferir_consulta', methods=['POST'])
def transferir_consulta():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE consulta
        SET crm = (SELECT crm FROM medico WHERE nomeM = 'Dr. Kildare'),
            data = '2024-05-24'
        WHERE idPac = (SELECT idPac FROM paciente WHERE nomeP = 'Diego Pituca')
            AND data = '2024-05-10'
            AND horaInicCon = '10:00:00'
            AND idEsp = (SELECT idEsp FROM especialidade WHERE nomeE = 'Dermatologia')
    """)
    conn.commit()
    cur.close()
    conn.close()
    
    # Verificando se a consulta foi transferida
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS consultas_transferidas
        FROM consulta
        WHERE crm = (SELECT crm FROM medico WHERE nomeM = 'Dr. Kildare')
            AND data = '2024-05-24'
            AND idPac = (SELECT idPac FROM paciente WHERE nomeP = 'Diego Pituca')
    """)
    results_transfer = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('index.html', results_transfer=results_transfer)



if __name__ == '__main__':
    init_tables()
    #init_values()
    app.run(debug=True)
