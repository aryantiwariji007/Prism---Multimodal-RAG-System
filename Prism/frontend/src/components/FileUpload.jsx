import { useCallback, useState } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Image, Mic, X, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const FileUpload = ({ onFileUpload, uploadedFiles }) => {
  const [uploading, setUploading] = useState(false)
  const [processingProgress, setProcessingProgress] = useState({})

  // Function to poll for processing progress
  const pollProgress = async (progressId, fileName) => {
    try {
      const response = await fetch(`http://localhost:8000/api/processing-status/${progressId}`)

      if (!response.ok) {
        console.error(`Progress polling failed for ${fileName}: ${response.status}`)
        return
      }

      const progress = await response.json()

      if (progress && progress.file_id) {
        setProcessingProgress(prev => ({
          ...prev,
          [progressId]: {
            status: progress.status || 'processing',
            percentage: progress.progress || 0,
            message: progress.current_step || 'Processing...'
          }
        }))

        // If completed or failed, stop polling
        if (progress.status === 'completed' || progress.status === 'error') {
          return
        }

        // Continue polling every 1 second
        setTimeout(() => pollProgress(progressId, fileName), 1000)
      }
    } catch (error) {
      console.error('Error polling progress:', error)
      // Set error state instead of failing silently
      setProcessingProgress(prev => ({
        ...prev,
        [progressId]: {
          status: 'error',
          percentage: 0,
          message: `Error checking progress: ${error.message}`
        }
      }))
    }
  }

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    try {
      setUploading(true);
      const uploadPromises = acceptedFiles.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
          const response = await fetch('http://localhost:8000/api/upload', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
          }

          const result = await response.json();

          // If we got a progress_id, start polling for progress
          if (result.success && result.progress_id) {
            setProcessingProgress(prev => ({
              ...prev,
              [result.progress_id]: {
                status: 'started',
                percentage: 0,
                message: 'Upload completed, starting processing...'
              }
            }))

            // Start polling for progress
            pollProgress(result.progress_id, file.name)
          }

          toast.success(`${file.name} uploaded successfully!`);

          // CRITICAL FIX: explicit copy of File properties + backend result
          // Spreading 'file' ({...file}) does NOT copy name, size, type in some browsers/contexts
          return {
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified,
            ...result
          };
        } catch (error) {
          console.error('Upload error:', error);
          toast.error(`Upload failed for ${file.name}: ${error.message}`);
          return null;
        }
      });

      const results = await Promise.all(uploadPromises);
      const successfulUploads = results.filter(result => result !== null);

      if (onFileUpload && successfulUploads.length > 0) {
        onFileUpload(successfulUploads);
      }
    } catch (error) {
      console.error('Critical upload error:', error);
      toast.error(`Critical error during upload: ${error.message}`);
    } finally {
      setUploading(false);
    }
  }, [onFileUpload]);

  // Recursive function to traverse file system entries
  const traverseFileTree = async (item, path = '') => {
    if (item.isFile) {
      return new Promise((resolve) => {
        item.file((file) => {
          // Add path info to file object for manual handling if needed
          file.filepath = path + file.name
          resolve([file])
        })
      })
    } else if (item.isDirectory) {
      const dirReader = item.createReader()
      const entries = await new Promise((resolve) => {
        dirReader.readEntries((entries) => resolve(entries))
      })

      const filePromises = entries.map(entry => traverseFileTree(entry, path + item.name + "/"))
      const fileArrays = await Promise.all(filePromises)
      // Flatten
      return fileArrays.reduce((acc, val) => acc.concat(val), [])
    }
    return []
  }

  // Custom drop handler to support folders
  const handleCustomDrop = useCallback(async (e) => {
    e.preventDefault()
    e.stopPropagation()

    const items = e.dataTransfer.items
    if (!items) return

    setUploading(true)
    const toastId = toast.loading("Scanning files...")

    try {
      const entryPromises = []
      // Note: DataTransferItemList is not an array, so we can't map
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null
        if (entry) {
          entryPromises.push(traverseFileTree(entry))
        }
      }

      const fileArrays = await Promise.all(entryPromises)
      const allFiles = fileArrays.reduce((acc, val) => acc.concat(val), [])

      toast.dismiss(toastId)

      if (allFiles.length === 0) {
        toast.error("No files found!")
        setUploading(false)
        return
      }

      // Group files by top-level folder
      // logic: if file path starts with "Folder/", we group them.
      // But traverseFileTree path is relative to the dropped item?
      // Wait, traverseFileTree(entry, path='') -> path becomes "FolderName/" for children.
      // So files inside "Policies" will have filepath "Policies/Doc.pdf".

      const filesByFolder = {}
      const rootFiles = []

      allFiles.forEach(file => {
        const pathParts = (file.filepath || file.name).split('/')
        if (pathParts.length > 1) {
          const folderName = pathParts[0]
          if (!filesByFolder[folderName]) filesByFolder[folderName] = []
          filesByFolder[folderName].push(file)
        } else {
          rootFiles.push(file)
        }
      })

      let totalUploaded = 0

      // 1. Upload folders
      for (const [folderName, folderFiles] of Object.entries(filesByFolder)) {
        try {
          // Create Folder
          const folderRes = await fetch('http://localhost:8000/api/folders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: folderName })
          });

          if (!folderRes.ok) throw new Error(`Failed to create folder ${folderName}`);
          const folderData = await folderRes.json();
          const folderId = folderData.folder.id;

          toast.success(`Created folder: ${folderName}`)

          // Upload files to this folder
          const uploadPromises = folderFiles.map(async (file) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('folder_id', folderId);

            try {
              const response = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData,
              });
              if (!response.ok) return null;

              const result = await response.json();
              if (result.success && result.progress_id) {
                // Progress tracking logic
                setProcessingProgress(prev => ({
                  ...prev,
                  [result.progress_id]: { status: 'started', percentage: 0, message: 'Processing...' }
                }))
                pollProgress(result.progress_id, file.name)
              }
              return result
            } catch (e) { return null }
          })

          const results = await Promise.all(uploadPromises)
          totalUploaded += results.filter(r => r).length

        } catch (err) {
          console.error(err)
          toast.error(`Failed to process folder ${folderName}`)
        }
      }

      // 2. Upload root files (no folder)
      if (rootFiles.length > 0) {
        const uploadPromises = rootFiles.map(async (file) => {
          const formData = new FormData();
          formData.append('file', file);

          try {
            const response = await fetch('http://localhost:8000/api/upload', {
              method: 'POST',
              body: formData,
            });
            if (!response.ok) return null;

            const result = await response.json();
            if (result.success && result.progress_id) {
              // Progress tracking logic
              setProcessingProgress(prev => ({
                ...prev,
                [result.progress_id]: { status: 'started', percentage: 0, message: 'Processing...' }
              }))
              pollProgress(result.progress_id, file.name)
            }
            return { name: file.name, size: file.size, type: file.type, ...result }
          } catch (e) { return null }
        })

        const results = await Promise.all(uploadPromises)
        const successful = results.filter(r => r)
        totalUploaded += successful.length
        if (onFileUpload) onFileUpload(successful)
      }

      toast.success(`Uploaded ${totalUploaded} files total!`)
      if (onFileUpload) {
        // Trigger refresh is a bit tricky here as we don't return all folder files in the callback usually
        // But we can trigger a refetch if needed or just let the user see the toast
        // Let's pass an empty array to trigger any effects if needed, or better, fetchFileCounts in parent
      }

    } catch (err) {
      console.error(err)
      toast.error("Upload failed")
    } finally {
      setUploading(false)
    }

  }, [onFileUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, // Fallback for click-select which uses standard onDrop
    noClick: false,
    noKeyboard: false,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'audio/*': ['.mp3', '.wav', '.m4a'],
      'video/*': ['.mp4', '.avi', '.mov', '.mkv'],
      'text/plain': ['.txt', '.md', '.log'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'text/xml': ['.xml'],
      'text/html': ['.html', '.htm'],
      'application/vnd.ms-powerpoint': ['.ppt', '.pptx']
    },
    multiple: true,
    maxSize: 100 * 1024 * 1024 // 100MB
  })

  // Intercept the root props to hook our custom drop handler
  const { onDrop: originalOnDrop, ...rootPropsRest } = getRootProps()
  const rootProps = {
    ...rootPropsRest,
    onDrop: handleCustomDrop // Override with our custom handler
  }

  const getFileIcon = (type) => {
    if (type.includes('image')) return <Image className="w-6 h-6 md:w-8 md:h-8 text-blue-500 flex-shrink-0" />
    if (type.includes('audio')) return <Mic className="w-6 h-6 md:w-8 md:h-8 text-green-500 flex-shrink-0" />
    return <FileText className="w-6 h-6 md:w-8 md:h-8 text-red-500 flex-shrink-0" />
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="search-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6 md:mb-8"
      >
        <h2 className="text-2xl md:text-3xl font-bold gradient-text mb-3 md:mb-4 px-2">
          Upload Your Documents
        </h2>
        <p className="text-sm md:text-base text-gray-600 max-w-2xl mx-auto px-2">
          Upload PDFs, Word documents, images, and audio files. All processing happens locally on your device.
        </p>
      </motion.div>

      {/* Upload Area */}
      <div className="flex gap-4 mb-4 justify-center">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => document.getElementById('folder-upload').click()}
          className="flex items-center space-x-2 px-6 py-3 bg-white border border-gray-300 rounded-xl hover:border-primary-500 hover:text-primary-600 transition-colors shadow-sm"
        >
          <Upload className="w-5 h-5" />
          <span className="font-medium">Upload Folder</span>
        </motion.button>
        <input
          id="folder-upload"
          type="file"
          webkitdirectory=""
          directory=""
          multiple
          className="hidden"
          onChange={async (e) => {
            const files = Array.from(e.target.files);
            if (files.length === 0) return;

            // 1. Determine Folder Name (top level)
            const firstFile = files[0];
            const folderName = firstFile.webkitRelativePath
              ? firstFile.webkitRelativePath.split('/')[0]
              : 'New Folder Upload';

            try {
              setUploading(true);
              // 2. Create the folder via API
              const folderRes = await fetch('http://localhost:8000/api/folders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: folderName })
              });

              if (!folderRes.ok) throw new Error("Failed to create folder");
              const folderData = await folderRes.json();
              const folderId = folderData.folder.id;

              toast.success(`Created folder: ${folderName}`);

              // 3. Upload all files assigned to this folder
              const BATCH_SIZE = 20;
              const results = [];

              for (let i = 0; i < files.length; i += BATCH_SIZE) {
                const batch = files.slice(i, i + BATCH_SIZE);
                // Update loading toast if possible, or just log

                const batchPromises = batch.map(async (file) => {
                  const formData = new FormData();
                  formData.append('file', file);
                  formData.append('folder_id', folderId); // Attach folder ID

                  try {
                    const response = await fetch('http://localhost:8000/api/upload', {
                      method: 'POST',
                      body: formData,
                    });

                    if (!response.ok) {
                      const errorData = await response.json();
                      throw new Error(errorData.detail || 'Upload failed');
                    }

                    const result = await response.json();

                    if (result.success && result.progress_id) {
                      setProcessingProgress(prev => ({
                        ...prev,
                        [result.progress_id]: {
                          status: 'started',
                          percentage: 0,
                          message: 'Upload completed, starting processing...'
                        }
                      }))
                      pollProgress(result.progress_id, file.name)
                    }

                    return {
                      name: file.name,
                      size: file.size,
                      type: file.type,
                      lastModified: file.lastModified,
                      ...result
                    };

                  } catch (error) {
                    console.error(`Upload error for ${file.name}:`, error);
                    return { error: true, name: file.name, reason: error.message };
                  }
                });

                const batchResults = await Promise.all(batchPromises);
                results.push(...batchResults);
              }
              const successfulUploads = results.filter(r => r && !r.error);
              const failedUploads = results.filter(r => r && r.error);

              if (onFileUpload && successfulUploads.length > 0) {
                onFileUpload(successfulUploads);
              }

              if (failedUploads.length > 0) {
                toast.error(`${failedUploads.length} files failed to upload. See console.`);
                console.warn("Failed files:", failedUploads);
              }

              toast.success(`Successfully uploaded ${successfulUploads.length} files to ${folderName}`);

            } catch (err) {
              console.error("Folder upload error:", err);
              toast.error(`Folder upload failed: ${err.message}`);
            } finally {
              setUploading(false);
              e.target.value = ''; // Reset input
            }
          }}
        />
      </div>

      <motion.div
        {...rootProps}
        className={`border-2 border-dashed rounded-2xl p-6 md:p-12 text-center cursor-pointer transition-all duration-300 ${isDragActive
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          } ${uploading ? 'pointer-events-none opacity-50' : ''}`}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center space-y-3 md:space-y-4">
          {uploading ? (
            <div className="w-12 h-12 md:w-16 md:h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
          ) : (
            <Upload className="w-12 h-12 md:w-16 md:h-16 text-gray-400" />
          )}

          <div>
            <h3 className="text-lg md:text-xl font-semibold text-gray-700 mb-2">
              {uploading ? 'Uploading...' : isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </h3>
            <p className="text-sm md:text-base text-gray-500 mb-3 md:mb-4">
              or click to browse individual files
            </p>

            <div className="flex flex-wrap justify-center gap-2 md:gap-4 text-xs md:text-sm text-gray-600">
              <div className="flex items-center space-x-1 md:space-x-2">
                <FileText className="w-3 h-3 md:w-4 md:h-4" />
                <span>PDF, DOCX</span>
              </div>
              <div className="flex items-center space-x-1 md:space-x-2">
                <Image className="w-3 h-3 md:w-4 md:h-4" />
                <span>Images</span>
              </div>
              <div className="flex items-center space-x-1 md:space-x-2">
                <Mic className="w-3 h-3 md:w-4 md:h-4" />
                <span>Audio</span>
              </div>
            </div>

            <p className="text-xs text-gray-400 mt-2">
              Maximum file size: 100MB
            </p>
          </div>
        </div>
      </motion.div>

      {/* Uploaded Files List */}
      {uploadedFiles && uploadedFiles.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8"
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span>Uploaded Files ({uploadedFiles.length})</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {uploadedFiles.map((file, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-50 rounded-lg p-4 border border-gray-200 card-hover"
              >
                <div className="flex items-start space-x-3">
                  {getFileIcon(file.type)}
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-gray-900 truncate" title={file.name}>
                      {file.name}
                    </h4>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                    <div className="mt-2">
                      {file.progress_id && processingProgress[file.progress_id] ? (
                        <div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all duration-300 ${processingProgress[file.progress_id].status === 'completed'
                                ? 'bg-green-500'
                                : processingProgress[file.progress_id].status === 'error'
                                  ? 'bg-red-500'
                                  : 'bg-blue-500'
                                }`}
                              style={{
                                width: `${processingProgress[file.progress_id].percentage || 0}%`
                              }}
                            ></div>
                          </div>
                          <p className={`text-xs mt-1 ${processingProgress[file.progress_id].status === 'completed'
                            ? 'text-green-600'
                            : processingProgress[file.progress_id].status === 'error'
                              ? 'text-red-600'
                              : 'text-blue-600'
                            }`}>
                            {processingProgress[file.progress_id].status === 'completed'
                              ? 'Processing completed!'
                              : processingProgress[file.progress_id].status === 'error'
                                ? `Error: ${processingProgress[file.progress_id].message}`
                                : processingProgress[file.progress_id].message || 'Processing...'}
                          </p>
                        </div>
                      ) : (
                        <div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-green-500 h-2 rounded-full w-full"></div>
                          </div>
                          <p className="text-xs text-green-600 mt-1">Uploaded</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default FileUpload