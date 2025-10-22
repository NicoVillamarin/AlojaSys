import React, { useState, useRef } from "react";
import { useCreate } from "src/hooks/useCreate";
import { bankTransferService } from "src/services/bankTransferService";
import SpinnerLoading from "src/components/SpinnerLoading";

export default function BankTransferForm({
  reservationId,
  amount,
  onSuccess,
  onError,
  onCancel,
  isBalancePayment = false
}) {
  const { mutate: createTransfer, isPending: isUploading } = useCreate({
    resource: 'payments/bank-transfers',
    onSuccess: (data) => {
      onSuccess?.(data);
    },
    onError: (error) => {
      onError?.(error);
    }
  });
  const [formData, setFormData] = useState({
    amount: amount || "",
    transfer_date: new Date().toISOString().split('T')[0], // Fecha actual
    cbu_iban: "",
    bank_name: "",
    notes: ""
  });
  const [receiptFile, setReceiptFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [errors, setErrors] = useState({});
  const fileInputRef = useRef(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Limpiar error del campo
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ""
      }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validar tipo de archivo
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
      if (!allowedTypes.includes(file.type)) {
        setErrors(prev => ({
          ...prev,
          receipt_file: "Solo se permiten archivos JPG, PNG o PDF"
        }));
        return;
      }

      // Validar tamaño (máximo 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setErrors(prev => ({
          ...prev,
          receipt_file: "El archivo no puede ser mayor a 10MB"
        }));
        return;
      }

      setReceiptFile(file);
      setErrors(prev => ({
        ...prev,
        receipt_file: ""
      }));

      // Crear preview para imágenes
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else {
        setPreviewUrl(null);
      }
    }
  };

  const removeFile = () => {
    setReceiptFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      newErrors.amount = "El monto debe ser mayor a 0";
    }

    if (!formData.transfer_date) {
      newErrors.transfer_date = "La fecha de transferencia es requerida";
    }

    if (!formData.cbu_iban) {
      newErrors.cbu_iban = "El CBU/IBAN es requerido";
    } else {
      const validation = bankTransferService.validateCbuIban(formData.cbu_iban);
      if (!validation.valid) {
        newErrors.cbu_iban = validation.message;
      }
    }

    if (!receiptFile) {
      newErrors.receipt_file = "El comprobante es requerido";
    } else {
      const validation = bankTransferService.validateReceiptFile(receiptFile);
      if (!validation.valid) {
        newErrors.receipt_file = validation.message;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setErrors({});

    try {
      // Convertir archivo a base64
      const fileBase64 = await convertFileToBase64(receiptFile);
      
      const transferData = {
        reservation: reservationId,
        amount: parseFloat(formData.amount),
        transfer_date: formData.transfer_date,
        cbu_iban: formData.cbu_iban,
        bank_name: formData.bank_name,
        notes: formData.notes,
        receipt_file_base64: fileBase64,
        receipt_filename: receiptFile.name
      };

      createTransfer(transferData);
    } catch (error) {
      console.error('Error convirtiendo archivo:', error);
      onError?.(error);
    }
  };

  const formatCurrency = (value) => {
    return bankTransferService.formatAmount(value);
  };

  return (
    <div className="space-y-6">
      {/* Información del pago */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">
          {isBalancePayment ? "Pago de Saldo Pendiente" : "Transferencia Bancaria"}
        </h3>
        <div className="text-sm text-blue-700">
          <p>Monto: <span className="font-semibold">{formatCurrency(formData.amount)}</span></p>
          <p>Reserva: #{reservationId}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Monto */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Monto de la Transferencia *
          </label>
          <input
            type="number"
            name="amount"
            value={formData.amount}
            onChange={handleInputChange}
            step="0.01"
            min="0.01"
            className={`w-full border rounded-md px-3 py-2 text-sm ${
              errors.amount ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="0.00"
            disabled={!!amount} // Si viene amount fijo, deshabilitar
          />
          {errors.amount && (
            <p className="text-red-500 text-xs mt-1">{errors.amount}</p>
          )}
        </div>

        {/* Fecha de transferencia */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Fecha de Transferencia *
          </label>
          <input
            type="date"
            name="transfer_date"
            value={formData.transfer_date}
            onChange={handleInputChange}
            max={new Date().toISOString().split('T')[0]} // No permitir fechas futuras
            className={`w-full border rounded-md px-3 py-2 text-sm ${
              errors.transfer_date ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.transfer_date && (
            <p className="text-red-500 text-xs mt-1">{errors.transfer_date}</p>
          )}
        </div>

        {/* CBU/IBAN */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            CBU/IBAN de Destino *
          </label>
          <input
            type="text"
            name="cbu_iban"
            value={formData.cbu_iban}
            onChange={handleInputChange}
            className={`w-full border rounded-md px-3 py-2 text-sm ${
              errors.cbu_iban ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="1234567890123456789012"
            maxLength="50"
          />
          <p className="text-xs text-gray-500 mt-1">
            Ingrese el CBU (22 dígitos) o IBAN de la cuenta destino
          </p>
          {errors.cbu_iban && (
            <p className="text-red-500 text-xs mt-1">{errors.cbu_iban}</p>
          )}
        </div>

        {/* Nombre del banco */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nombre del Banco (Opcional)
          </label>
          <input
            type="text"
            name="bank_name"
            value={formData.bank_name}
            onChange={handleInputChange}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            placeholder="Ej: Banco Santander"
            maxLength="100"
          />
        </div>

        {/* Comprobante */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Comprobante de Transferencia *
          </label>
          <div className="space-y-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,.pdf"
              onChange={handleFileChange}
              className={`w-full border rounded-md px-3 py-2 text-sm ${
                errors.receipt_file ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {receiptFile && (
              <div className="flex items-center justify-between bg-gray-50 rounded-md p-2">
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-sm text-gray-700">{receiptFile.name}</span>
                  <span className="text-xs text-gray-500">
                    ({(receiptFile.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={removeFile}
                  className="text-red-500 hover:text-red-700"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            )}
            {previewUrl && (
              <div className="mt-2">
                <img
                  src={previewUrl}
                  alt="Preview del comprobante"
                  className="max-w-xs max-h-32 object-contain border rounded"
                />
              </div>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Formatos permitidos: JPG, PNG, PDF. Tamaño máximo: 10MB
          </p>
          {errors.receipt_file && (
            <p className="text-red-500 text-xs mt-1">{errors.receipt_file}</p>
          )}
        </div>

        {/* Notas */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notas Adicionales (Opcional)
          </label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            rows={3}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            placeholder="Información adicional sobre la transferencia..."
            maxLength="500"
          />
        </div>

        {/* Botones */}
        <div className="flex space-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600 transition"
            disabled={isUploading}
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={isUploading}
            className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition disabled:opacity-50"
          >
            {isUploading ? (
              <div className="flex items-center justify-center">
                <SpinnerLoading size={16} className="mr-2" />
                Subiendo...
              </div>
            ) : (
              "Subir Comprobante"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
