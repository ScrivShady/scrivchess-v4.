import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface FileUploaderProps {
  value?: string; // base64 string
  onChange: (base64: string | undefined) => void;
}

export function FileUploader({ value, onChange }: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File) => {
    // Basic validation for image type
    if (!file.type.startsWith('image/')) return;
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result as string;
      onChange(base64String);
    };
    reader.onerror = () => {
      console.error("FileReader error");
    };
    reader.readAsDataURL(file);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  if (value) {
    return (
      <div className="relative rounded-xl overflow-hidden border-2 border-border group bg-muted/20 flex items-center justify-center min-h-[300px]">
        <img src={value} alt="Preview" className="max-h-[400px] object-contain" />
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-sm">
          <Button 
            variant="destructive" 
            size="sm" 
            onClick={(e) => {
              e.stopPropagation();
              onChange(undefined);
              if (inputRef.current) inputRef.current.value = '';
            }}
            className="flex items-center gap-2"
          >
            <X className="w-4 h-4" /> Remove Image
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`
        border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 cursor-pointer
        flex flex-col items-center justify-center min-h-[300px]
        ${isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-muted/30'}
      `}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input 
        type="file" 
        className="hidden" 
        ref={inputRef}
        accept="image/jpeg,image/png,image/jpg"
        onChange={handleInputChange}
      />
      
      <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4 text-muted-foreground shadow-inner">
        <UploadCloud className="w-8 h-8" />
      </div>
      <h3 className="text-xl font-display font-semibold text-foreground mb-2">Upload Screenshot</h3>
      <p className="text-sm text-muted-foreground max-w-xs mx-auto mb-6">
        Drag and drop your chess game screenshot here, or click to browse files.
      </p>
      
      <Button variant="secondary" className="pointer-events-none">
        <ImageIcon className="w-4 h-4 mr-2" />
        Select File
      </Button>
    </div>
  );
}
