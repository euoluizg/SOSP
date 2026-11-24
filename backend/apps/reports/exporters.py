"""
SOSP — Exportadores Polimórficos de Relatórios (RF-14 / POO).

Implementa os 4 Pilares de Programação Orientada a Objetos:
- Abstração: classe base abstrata `ReportExporter(abc.ABC)` com contrato formal.
- Herança: `CsvExporter` e `PdfExporter` herdam de `ReportExporter`.
- Encapsulamento: serialização e escapamento encapsulados em cada estratégia concreta.
- Polimorfismo: `ReportsService` e `get_report_exporter` operam sobre a interface comum `ReportExporter`.
"""

import abc
import csv
import io
from typing import Any, Dict, Type

from common.exceptions import ProblemDetailsException


class ReportExporter(abc.ABC):
    """Contrato abstrato para estratégias de exportação de relatórios gerenciais (RF-14)."""

    @property
    @abc.abstractmethod
    def format_name(self) -> str:
        """Identificador canônico do formato (ex.: 'csv', 'pdf')."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def content_type(self) -> str:
        """MIME type oficial do arquivo exportado."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def file_extension(self) -> str:
        """Extensão de arquivo sem ponto (ex.: 'csv', 'pdf')."""
        raise NotImplementedError

    @abc.abstractmethod
    def export(self, summary: Dict[str, Any]) -> bytes:
        """Serializa o resumo consolidado de agendamentos no formato da subclasse."""
        raise NotImplementedError

    def build_filename(self, prefix: str = "relatorio-agendamentos") -> str:
        """Gera o nome padronizado do arquivo exportado."""
        return f"{prefix}.{self.file_extension}"


class CsvExporter(ReportExporter):
    """Exportador concreto de relatórios em formato CSV UTF-8."""

    @property
    def format_name(self) -> str:
        return "csv"

    @property
    def content_type(self) -> str:
        return "text/csv; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return "csv"

    def export(self, summary: Dict[str, Any]) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        metrics = summary.get("metrics") or {}
        period = summary.get("period") or {}
        writer.writerow(["Relatorio", "PeriodoInicio", "PeriodoFim", "Total", "Agendados", "EmAtendimento", "Concluidos", "Cancelados", "Ausentes", "TaxaComparecimento"])
        writer.writerow([
            "SOSP - Relatorio de Agendamentos",
            period.get("start", ""),
            period.get("end", ""),
            metrics.get("totalAppointments", 0),
            metrics.get("scheduled", 0),
            metrics.get("inProgress", 0),
            metrics.get("completed", 0),
            metrics.get("cancelled", 0),
            metrics.get("noShow", 0),
            metrics.get("attendanceRate", 0),
        ])

        writer.writerow([])
        writer.writerow(["Servico", "Total", "Concluidos", "Ausentes"])
        for row in summary.get("byService") or []:
            writer.writerow([
                row.get("serviceName", "Servico Publico"),
                row.get("total", 0),
                row.get("completed", 0),
                row.get("noShow", 0),
            ])

        return buffer.getvalue().encode("utf-8")


class PdfExporter(ReportExporter):
    """Exportador concreto de relatórios em formato PDF 1.4."""

    @property
    def format_name(self) -> str:
        return "pdf"

    @property
    def content_type(self) -> str:
        return "application/pdf"

    @property
    def file_extension(self) -> str:
        return "pdf"

    @staticmethod
    def _escape_pdf_text(text: str) -> str:
        ascii_safe = text.encode("latin-1", "replace").decode("latin-1")
        return ascii_safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def export(self, summary: Dict[str, Any]) -> bytes:
        metrics = summary.get("metrics") or {}
        period = summary.get("period") or {}
        lines = [
            "SOSP - Relatorio Consolidado de Agendamentos",
            f"Periodo: {period.get('start', '')} a {period.get('end', '')}",
            f"Total: {metrics.get('totalAppointments', 0)} | Concluidos: {metrics.get('completed', 0)} | Ausentes: {metrics.get('noShow', 0)}",
            f"Taxa de comparecimento: {metrics.get('attendanceRate', 0)}%",
        ]
        for row in (summary.get("byService") or [])[:15]:
            lines.append(
                f"- {row.get('serviceName', 'Servico')}: total={row.get('total', 0)}, concluidos={row.get('completed', 0)}"
            )

        content_ops = ["BT", "/F1 11 Tf", "50 760 Td"]
        for idx, line in enumerate(lines):
            escaped = self._escape_pdf_text(line)
            if idx > 0:
                content_ops.append("0 -16 Td")
            content_ops.append(f"({escaped}) Tj")
        content_ops.append("ET")
        stream_data = "\n".join(content_ops).encode("latin-1")

        objects = [
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
            b"4 0 obj << /Length " + str(len(stream_data)).encode("ascii") + b" >> stream\n" + stream_data + b"\nendstream endobj\n",
            b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        ]

        out = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for obj in objects:
            offsets.append(len(out))
            out.extend(obj)

        xref_pos = len(out)
        out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        out.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
        out.extend(
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
        )
        return bytes(out)


_EXPORTER_REGISTRY: Dict[str, Type[ReportExporter]] = {
    "csv": CsvExporter,
    "pdf": PdfExporter,
}


def get_report_exporter(export_type: str) -> ReportExporter:
    """Fábrica polimórfica que instancia o exportador correspondente ao formato solicitado."""
    normalized = (export_type or "csv").strip().lower()
    exporter_cls = _EXPORTER_REGISTRY.get(normalized)
    if exporter_cls is None:
        raise ProblemDetailsException(
            detail=f"Formato de exportação '{export_type}' não suportado. Utilize 'csv' ou 'pdf'.",
            title="Formato de Exportação Inválido",
            status_code=400,
            errors=[{"field": "type", "message": "Formato de exportação deve ser 'csv' ou 'pdf'."}],
        )
    return exporter_cls()
