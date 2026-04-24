export function mergeSelectedFiles(existingFiles: File[], incomingFiles: File[]): File[] {
  const deduped = new Map<string, File>();

  for (const file of [...existingFiles, ...incomingFiles]) {
    deduped.set(createFileKey(file), file);
  }

  return Array.from(deduped.values());
}

function createFileKey(file: File) {
  return [file.name, file.size, file.lastModified].join(":");
}
