"use client";

import { useState, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Upload, CheckCircle2, Loader2, AlertCircle, Image } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";

const batchUploadSchema = z.object({
  batchId: z.string().min(3, "Identificador deve ter no mínimo 3 caracteres"),
  productId: z.string().min(1, "Produto é obrigatório"),
  declaredQuantity: z.number().min(1, "Quantidade deve ser no mínimo 1"),
  manufactureDate: z.string().min(1, "Data de fabricação é obrigatória"),
  expirationDate: z.string().optional(),
  destination: z.string().optional(),
  csvFile: z
    .any()
    .refine((val: FileList | undefined) => val?.length === 1, "Arquivo CSV é obrigatório")
    .refine((val: FileList | undefined) => val?.[0]?.name?.endsWith(".csv"), "O arquivo deve ser CSV"),
  imageZipFile: z
    .any()
    .optional()
    .refine(
      (val: FileList | undefined) => !val?.length || val[0]?.name?.endsWith(".zip"),
      "O arquivo deve ser .zip (imagens compactadas)"
    ),
});

export type BatchUploadFormValues = z.infer<typeof batchUploadSchema>;

type FlowState = "idle" | "uploading" | "processing" | "success" | "error";

export function BatchUploadForm() {
  const [flowState, setFlowState] = useState<FlowState>("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<BatchUploadFormValues>({
    resolver: zodResolver(batchUploadSchema),
    defaultValues: {
      batchId: "",
      productId: "",
      declaredQuantity: 1,
      manufactureDate: "",
      expirationDate: "",
      destination: "",
    },
  });

  const csvFile = watch("csvFile");
  const fileName = csvFile?.length ? csvFile[0]?.name : null;
  const imageZipFile = watch("imageZipFile");
  const imageZipFileName = imageZipFile?.length ? imageZipFile[0]?.name : null;

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file?.name.endsWith(".csv")) {
        const dt = new DataTransfer();
        dt.items.add(file);
        setValue("csvFile", dt.files, { shouldValidate: true });
      }
    },
    [setValue]
  );

  const onDropImageZip = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file?.name.endsWith(".zip")) {
        const dt = new DataTransfer();
        dt.items.add(file);
        setValue("imageZipFile", dt.files, { shouldValidate: true });
      }
    },
    [setValue]
  );

  const onDragOver = (e: React.DragEvent) => e.preventDefault();

  const onSubmit = async (data: BatchUploadFormValues) => {
    setFlowState("uploading");
    setErrorMessage(null);
    setUploadProgress(0);

    // Simulate upload progress (mock)
    for (let p = 0; p <= 100; p += 10) {
      await new Promise((r) => setTimeout(r, 80));
      setUploadProgress(p);
    }

    setFlowState("processing");

    // Mock Merkle Tree / hashes processing (3 seconds)
    await new Promise((r) => setTimeout(r, 3000));

    setFlowState("success");
  };

  const resetForm = () => {
    setFlowState("idle");
    setUploadProgress(0);
    setErrorMessage(null);
  };

  const inputBase =
    "mt-1 w-full rounded-lg border border-graphite-300 bg-white px-4 py-2.5 text-sm text-graphite-900 placeholder-graphite-400 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white dark:placeholder-graphite-500";

  const labelBase = "block text-sm font-medium text-graphite-700 dark:text-graphite-300";

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold text-graphite-900 dark:text-white">
          Novo Lote
        </h3>
        <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
          Preencha os dados do lote e envie o arquivo CSV com os UUIDs.
        </p>
      </CardHeader>
      <CardContent>
        {flowState === "success" ? (
          <div className="rounded-xl border border-success/30 bg-success/5 p-6 dark:border-success/30 dark:bg-success/10">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-10 w-10 flex-shrink-0 text-success" />
              <div>
                <h4 className="font-semibold text-graphite-900 dark:text-white">
                  Lote registrado com sucesso
                </h4>
                <p className="mt-1 text-sm text-graphite-600 dark:text-graphite-400">
                  O Merkle Tree e os hashes de segurança foram calculados. O lote está pronto para uso.
                </p>
                <button
                  type="button"
                  onClick={resetForm}
                  className="mt-4 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-500"
                >
                  Registrar outro lote
                </button>
              </div>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <label htmlFor="batchId" className={labelBase}>
                  Identificador do Lote
                </label>
                <input
                  id="batchId"
                  type="text"
                  placeholder="LOTE-AGRO-001"
                  className={inputBase}
                  {...register("batchId")}
                />
                {errors.batchId && (
                  <p className="mt-1 flex items-center gap-1 text-sm text-alert">
                    <AlertCircle className="h-4 w-4" />
                    {String(errors.batchId.message ?? "")}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="productId" className={labelBase}>
                  Produto Base
                </label>
                <input
                  id="productId"
                  type="text"
                  placeholder="Ex: Galão 5L - Herbicida X"
                  className={inputBase}
                  {...register("productId")}
                />
                {errors.productId && (
                  <p className="mt-1 flex items-center gap-1 text-sm text-alert">
                    <AlertCircle className="h-4 w-4" />
                    {String(errors.productId.message ?? "")}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="declaredQuantity" className={labelBase}>
                  Quantidade Declarada
                </label>
                <input
                  id="declaredQuantity"
                  type="number"
                  min={1}
                  className={inputBase}
                  {...register("declaredQuantity", { valueAsNumber: true })}
                />
                {errors.declaredQuantity && (
                  <p className="mt-1 flex items-center gap-1 text-sm text-alert">
                    <AlertCircle className="h-4 w-4" />
                    {String(errors.declaredQuantity.message ?? "")}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="manufactureDate" className={labelBase}>
                  Data de Fabricação
                </label>
                <input
                  id="manufactureDate"
                  type="date"
                  className={inputBase}
                  {...register("manufactureDate")}
                />
                {errors.manufactureDate && (
                  <p className="mt-1 flex items-center gap-1 text-sm text-alert">
                    <AlertCircle className="h-4 w-4" />
                    {String(errors.manufactureDate.message ?? "")}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="expirationDate" className={labelBase}>
                  Data de Validade (opcional)
                </label>
                <input
                  id="expirationDate"
                  type="date"
                  className={inputBase}
                  {...register("expirationDate")}
                />
              </div>

              <div className="sm:col-span-2">
                <label htmlFor="destination" className={labelBase}>
                  Destino Geográfico (opcional)
                </label>
                <input
                  id="destination"
                  type="text"
                  placeholder="Ex: Distribuidor MATOPIBA"
                  className={inputBase}
                  {...register("destination")}
                />
              </div>
            </div>

            <div>
              <label className={labelBase}>Arquivo CSV (UUIDs)</label>
              <div
                onDrop={onDrop}
                onDragOver={onDragOver}
                className={`mt-2 flex flex-col items-center justify-center rounded-xl border-2 border-dashed py-12 transition-colors ${
                  fileName
                    ? "border-primary-300 bg-primary-50/50 dark:border-primary-600/50 dark:bg-primary-500/5"
                    : "border-graphite-300 bg-graphite-50/50 hover:border-primary-400 dark:border-graphite-700 dark:bg-graphite-900/50 dark:hover:border-primary-500"
                }`}
              >
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  id="csv-upload"
                  {...register("csvFile")}
                />
                <label
                  htmlFor="csv-upload"
                  className="flex cursor-pointer flex-col items-center gap-2"
                >
                  <Upload className="h-10 w-10 text-graphite-400 dark:text-graphite-500" />
                  <span className="text-sm font-medium text-graphite-700 dark:text-graphite-300">
                    {fileName ? fileName : "Arraste o arquivo aqui ou clique para selecionar"}
                  </span>
                  <span className="text-xs text-graphite-500 dark:text-graphite-400">
                    Apenas arquivos .csv
                  </span>
                </label>
              </div>
              {errors.csvFile && (
                <p className="mt-1 flex items-center gap-1 text-sm text-alert">
                  <AlertCircle className="h-4 w-4" />
                  {String(errors.csvFile.message ?? "")}
                </p>
              )}
            </div>

            <div>
              <label className={labelBase}>Imagens (arquivo .zip compactado)</label>
              <div
                onDrop={onDropImageZip}
                onDragOver={onDragOver}
                className={`mt-2 flex flex-col items-center justify-center rounded-xl border-2 border-dashed py-12 transition-colors ${
                  imageZipFileName
                    ? "border-primary-300 bg-primary-50/50 dark:border-primary-600/50 dark:bg-primary-500/5"
                    : "border-graphite-300 bg-graphite-50/50 hover:border-primary-400 dark:border-graphite-700 dark:bg-graphite-900/50 dark:hover:border-primary-500"
                }`}
              >
                <input
                  type="file"
                  accept=".zip"
                  className="hidden"
                  id="image-zip-upload"
                  {...register("imageZipFile")}
                />
                <label
                  htmlFor="image-zip-upload"
                  className="flex cursor-pointer flex-col items-center gap-2"
                >
                  <Image className="h-10 w-10 text-graphite-400 dark:text-graphite-500" />
                  <span className="text-sm font-medium text-graphite-700 dark:text-graphite-300">
                    {imageZipFileName
                      ? imageZipFileName
                      : "Arraste o arquivo .zip aqui ou clique para selecionar"}
                  </span>
                  <span className="text-xs text-graphite-500 dark:text-graphite-400">
                    Imagens compactadas em .zip
                  </span>
                </label>
              </div>
              {errors.imageZipFile && (
                <p className="mt-1 flex items-center gap-1 text-sm text-alert">
                  <AlertCircle className="h-4 w-4" />
                  {String(errors.imageZipFile.message ?? "")}
                </p>
              )}
            </div>

            {flowState === "uploading" && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-graphite-700 dark:text-graphite-300">
                  Enviando arquivo...
                </p>
                <div className="h-2 w-full overflow-hidden rounded-full bg-graphite-200 dark:bg-graphite-800">
                  <div
                    className="h-full bg-primary-600 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {flowState === "processing" && (
              <div className="flex items-center gap-3 rounded-lg border border-graphite-200 bg-graphite-50 p-4 dark:border-graphite-800 dark:bg-graphite-900/50">
                <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                <p className="text-sm font-medium text-graphite-700 dark:text-graphite-300">
                  Calculando Merkle Tree e hashes de segurança...
                </p>
              </div>
            )}

            {errorMessage && (
              <div className="flex items-center gap-2 rounded-lg border border-alert/30 bg-alert/10 p-3 text-sm text-alert">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                {errorMessage}
              </div>
            )}

            {flowState === "idle" && (
              <button
                type="submit"
                className="w-full rounded-lg bg-primary-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-graphite-900"
              >
                Registrar Lote
              </button>
            )}
          </form>
        )}
      </CardContent>
    </Card>
  );
}
