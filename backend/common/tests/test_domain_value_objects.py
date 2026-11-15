import unittest
from common.domain.value_objects import CpfDocument, RegistrationNumber, ProtocolCode


class TestDomainValueObjects(unittest.TestCase):
    """Testes unitários dos Objetos de Valor e Encapsulamento de Domínio (POO)."""

    def test_cpf_document_valid(self):
        # CPF válido conhecido com dígitos verificadores matematicamente corretos
        cpf = CpfDocument("111.444.777-35")
        self.assertEqual(cpf.clean_value, "11144477735")
        self.assertEqual(cpf.formatted, "111.444.777-35")
        self.assertEqual(cpf.masked, "***.444.777-**")
        self.assertEqual(str(cpf), "111.444.777-35")

    def test_cpf_document_equality(self):
        cpf1 = CpfDocument("11144477735")
        cpf2 = CpfDocument("111.444.777-35")
        self.assertEqual(cpf1, cpf2)
        self.assertEqual(cpf1, "11144477735")

    def test_cpf_document_rejects_repeated_digits(self):
        with self.assertRaises(ValueError):
            CpfDocument("111.111.111-11")

    def test_cpf_document_rejects_invalid_checksum(self):
        with self.assertRaises(ValueError):
            CpfDocument("111.444.777-99")

    def test_cpf_document_rejects_invalid_length(self):
        with self.assertRaises(ValueError):
            CpfDocument("123.456")

    def test_registration_number_valid(self):
        reg = RegistrationNumber("ssp-1001")
        self.assertEqual(reg.value, "SSP-1001")
        self.assertEqual(reg.prefix, "SSP")
        self.assertEqual(str(reg), "SSP-1001")

        reg_year = RegistrationNumber("2026-9921")
        self.assertEqual(reg_year.value, "2026-9921")
        self.assertEqual(reg_year.prefix, "2026")

        reg_plain = RegistrationNumber("202XXXXX")
        self.assertEqual(reg_plain.value, "202XXXXX")
        self.assertIsNone(reg_plain.prefix)

    def test_registration_number_invalid(self):
        with self.assertRaises(ValueError):
            RegistrationNumber("AB")  # Curto demais (< 4 chars)

        with self.assertRaises(ValueError):
            RegistrationNumber("INV@LID#MATRICULA")

    def test_protocol_code_valid(self):
        protocol = ProtocolCode("20261105-1042")
        self.assertEqual(protocol.value, "20261105-1042")
        self.assertEqual(protocol.year, 2026)
        self.assertEqual(protocol.month, 11)
        self.assertEqual(protocol.day, 5)
        self.assertEqual(protocol.sequence_number, 1042)

    def test_protocol_code_invalid(self):
        with self.assertRaises(ValueError):
            ProtocolCode("2026-1042")

        with self.assertRaises(ValueError):
            ProtocolCode("ABCDEFGH-1042")


if __name__ == "__main__":
    unittest.main()
