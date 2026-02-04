import { useMemo } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

export default function PaymentReturn() {
  const { result } = useParams();
  const [searchParams] = useSearchParams();

  const mpPaymentId = searchParams.get("payment_id") || searchParams.get("collection_id");
  const status = searchParams.get("status");
  const externalReference = searchParams.get("external_reference");

  const view = useMemo(() => {
    const r = String(result || "").toLowerCase();
    if (r === "success") {
      return {
        title: "Pago recibido",
        subtitle: "Gracias. Si el pago fue aprobado, la reserva se actualizará automáticamente en unos instantes.",
        tone: "success",
      };
    }
    if (r === "failure") {
      return {
        title: "Pago no completado",
        subtitle: "El pago fue cancelado o rechazado. Podés intentar nuevamente con otro medio de pago.",
        tone: "danger",
      };
    }
    return {
      title: "Pago en proceso",
      subtitle: "Tu pago está en proceso. Te avisaremos cuando se acredite.",
      tone: "info",
    };
  }, [result]);

  const toneClasses =
    view.tone === "success"
      ? "border-green-200 bg-green-50 text-green-800"
      : view.tone === "danger"
      ? "border-red-200 bg-red-50 text-red-800"
      : "border-blue-200 bg-blue-50 text-blue-800";

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-white to-aloja-navy/5">
      <div className="w-full max-w-lg rounded-xl border bg-white shadow-sm p-6">
        <div className={`rounded-lg border p-4 ${toneClasses}`}>
          <div className="text-lg font-semibold">{view.title}</div>
          <div className="text-sm mt-1">{view.subtitle}</div>
        </div>

        {(mpPaymentId || status || externalReference) && (
          <div className="mt-4 text-xs text-gray-600 space-y-1">
            {status ? (
              <div>
                <span className="font-semibold">Estado:</span> {status}
              </div>
            ) : null}
            {mpPaymentId ? (
              <div>
                <span className="font-semibold">Pago:</span> {mpPaymentId}
              </div>
            ) : null}
            {externalReference ? (
              <div className="break-words">
                <span className="font-semibold">Referencia:</span> {externalReference}
              </div>
            ) : null}
          </div>
        )}

        <div className="mt-6 flex items-center justify-between gap-3">
          <Link
            to="/login"
            className="inline-flex items-center justify-center rounded-md border border-gray-200 px-4 py-2 text-sm hover:bg-gray-50"
          >
            Ir a AlojaSys
          </Link>
          <button
            type="button"
            onClick={() => {
              try {
                window.close();
              } catch {}
            }}
            className="inline-flex items-center justify-center rounded-md bg-aloja-navy px-4 py-2 text-sm text-white hover:opacity-95"
          >
            Cerrar esta ventana
          </button>
        </div>
      </div>
    </div>
  );
}

