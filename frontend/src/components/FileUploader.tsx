import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from './Button';

interface FileUploaderProps {
  accept: string;
  onUpload: (file: File) => Promise<void>;
  title: string;
  subtitle: string;
  supportedFormatsText: string;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  accept,
  onUpload,
  title,
  subtitle,
  supportedFormatsText,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    setStatusMessage(null);
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setStatusMessage(null);

    try {
      await onUpload(selectedFile);
      setStatusMessage({
        type: 'success',
        text: `Successfully uploaded '${selectedFile.name}'!`,
      });
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || 'File upload failed.';
      setStatusMessage({
        type: 'error',
        text: errorMsg,
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-blue-500 bg-blue-50/50'
            : selectedFile
            ? 'border-emerald-300 bg-emerald-50/30'
            : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileChange(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-full">
            <UploadCloud className="w-8 h-8" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 text-lg">{title}</h3>
            <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
          </div>
          <p className="text-xs font-medium text-slate-400">
            Supported: {supportedFormatsText}
          </p>

          {selectedFile && (
            <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm mt-3">
              <File className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-slate-700">
                {selectedFile.name}
              </span>
              <span className="text-xs text-slate-400">
                ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
            </div>
          )}
        </div>
      </div>

      {selectedFile && (
        <div className="mt-4 flex justify-end">
          <Button
            onClick={handleSubmit}
            isLoading={uploading}
            variant="primary"
            size="md"
          >
            Upload Document
          </Button>
        </div>
      )}

      {statusMessage && (
        <div
          className={`mt-4 p-4 rounded-lg flex items-center space-x-3 ${
            statusMessage.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          )}
          <span className="text-sm font-medium">{statusMessage.text}</span>
        </div>
      )}
    </div>
  );
};
