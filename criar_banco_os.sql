-- Tabela: Consultor
CREATE TABLE IF NOT EXISTS Consultor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    permissao TEXT NOT NULL CHECK(permissao IN ('consultor', 'supervisor'))
);

-- Tabela: Cliente
CREATE TABLE IF NOT EXISTS Cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE,
    telefone TEXT
);

-- Tabela: TipoMaquina
CREATE TABLE IF NOT EXISTS TipoMaquina (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL UNIQUE
);

-- Tabela: Modelo
CREATE TABLE IF NOT EXISTS Modelo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_modelo TEXT NOT NULL UNIQUE,
    chassi TEXT,
    tipo_maquina_id INTEGER,
    FOREIGN KEY (tipo_maquina_id) REFERENCES TipoMaquina(id)
);

-- Tabela: Status
CREATE TABLE IF NOT EXISTS Status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL UNIQUE
);

-- Tabela: OrdemDeServico
CREATE TABLE IF NOT EXISTS OrdemDeServico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_os TEXT NOT NULL UNIQUE,
    tipo_os TEXT NOT NULL,
    cliente_id INTEGER NOT NULL,
    modelo_id INTEGER NOT NULL,
    consultor_id INTEGER NOT NULL,
    status_id INTEGER NOT NULL,
    descricao_servico TEXT,
    data_abertura DATE,
    data_faturamento DATE,
    data_pagamento_fabrica DATE,
    valor_liquido REAL, -- ALTERADO: De TEXT para REAL
    FOREIGN KEY (cliente_id) REFERENCES Cliente(id),
    FOREIGN KEY (modelo_id) REFERENCES Modelo(id),
    FOREIGN KEY (consultor_id) REFERENCES Consultor(id),
    FOREIGN KEY (status_id) REFERENCES Status(id)
);