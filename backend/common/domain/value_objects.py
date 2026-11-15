"""
SOSP — Objetos de Valor de Domínio (Value Objects — POO / Encapsulamento)
Implementa o Pilar de Encapsulamento com atributos privados (_valor),
validação estrita de invariantes no construtor e propriedades imutáveis (@property).
"""

import re
from typing import Optional


class CpfDocument:
    """
    Objeto de Valor que encapsula as regras de integridade e formatação de CPF.
    Pilar: Encapsulamento de regras de negócio e imutabilidade.
    """

    def __init__(self, raw_cpf: str):
        if not raw_cpf or not isinstance(raw_cpf, str):
            raise ValueError("O CPF deve ser uma cadeia de texto não vazia.")

        digits = "".join(filter(str.isdigit, raw_cpf))
        if len(digits) != 11:
            raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")

        # Rejeita sequências com todos os dígitos repetidos
        if len(set(digits)) == 1:
            raise ValueError("CPF inválido: sequência de dígitos repetidos.")

        # Validação matemática dos dígitos verificadores
        for i in range(9, 11):
            val = sum((int(digits[num]) * ((i + 1) - num)) for num in range(0, i))
            digit = ((val * 10) % 11) % 10
            if int(digits[i]) != digit:
                raise ValueError("CPF inválido: dígitos verificadores inconsistentes.")

        self._digits: str = digits

    @property
    def clean_value(self) -> str:
        """Retorna apenas os 11 dígitos numéricos limpos."""
        return self._digits

    @property
    def formatted(self) -> str:
        """Retorna o CPF formatado no padrão oficial XXX.XXX.XXX-XX."""
        d = self._digits
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"

    @property
    def masked(self) -> str:
        """Retorna versão mascarada para exibição pública conforme LGPD: ***.XXX.XXX-**."""
        d = self._digits
        return f"***.{d[3:6]}.{d[6:9]}-**"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CpfDocument):
            return self._digits == other._digits
        if isinstance(other, str):
            return self._digits == "".join(filter(str.isdigit, other))
        return False

    def __repr__(self) -> str:
        return f"CpfDocument(clean_value='{self._digits}')"

    def __str__(self) -> str:
        return self.formatted


class RegistrationNumber:
    """
    Objeto de Valor que encapsula a matrícula funcional de servidores e gestores (ex: 202XXXXX, SSP-1001).
    Pilar: Encapsulamento e integridade de identificação institucional.
    """

    _PATTERN = re.compile(r"^[A-Za-z0-9-]{4,20}$")

    def __init__(self, raw_registration: str):
        if not raw_registration or not isinstance(raw_registration, str):
            raise ValueError("A matrícula funcional deve ser informada.")

        cleaned = raw_registration.strip().upper()
        if not self._PATTERN.match(cleaned):
            raise ValueError(
                f"Matrícula '{raw_registration}' inválida. Deve conter de 4 a 20 caracteres alfanuméricos ou hífen."
            )

        self._value: str = cleaned

    @property
    def value(self) -> str:
        """Retorna o valor normalizado em caixa alta."""
        return self._value

    @property
    def prefix(self) -> Optional[str]:
        """Retorna o prefixo do órgão/ano se houver hífen (ex: 'SSP' em 'SSP-1001', '2026' em '2026-9921')."""
        if "-" in self._value:
            return self._value.split("-", 1)[0]
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RegistrationNumber):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other.strip().upper()
        return False

    def __repr__(self) -> str:
        return f"RegistrationNumber(value='{self._value}')"

    def __str__(self) -> str:
        return self._value


class ProtocolCode:
    """
    Objeto de Valor para Protocolos de Atendimento no formato AAAAMMDD-XXXX (RN-20).
    Pilar: Encapsulamento de formato oficial e extração de data/sequência.
    """

    _PATTERN = re.compile(r"^(\d{8})-(\d{4})$")

    def __init__(self, raw_protocol: str):
        if not raw_protocol or not isinstance(raw_protocol, str):
            raise ValueError("O protocolo deve ser uma cadeia de texto não vazia.")

        match = self._PATTERN.match(raw_protocol.strip())
        if not match:
            raise ValueError(
                f"Protocolo '{raw_protocol}' inválido. O formato oficial deve ser AAAAMMDD-XXXX (RN-20)."
            )

        self._full: str = raw_protocol.strip()
        self._date_part: str = match.group(1)
        self._seq_part: str = match.group(2)

    @property
    def value(self) -> str:
        return self._full

    @property
    def year(self) -> int:
        return int(self._date_part[:4])

    @property
    def month(self) -> int:
        return int(self._date_part[4:6])

    @property
    def day(self) -> int:
        return int(self._date_part[6:8])

    @property
    def sequence_number(self) -> int:
        return int(self._seq_part)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ProtocolCode):
            return self._full == other._full
        if isinstance(other, str):
            return self._full == other.strip()
        return False

    def __repr__(self) -> str:
        return f"ProtocolCode(value='{self._full}')"

    def __str__(self) -> str:
        return self._full

