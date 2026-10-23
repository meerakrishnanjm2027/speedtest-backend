// Example logic for your React component
const testDownload = async () => {
  const config = await fetch(`${API_URL}/config`).then(r => r.json());
  const threadCount = config.download.threads; // Usually 4
  const testSize = 25000000; // 25MB per thread
  
  const startTime = performance.now();
  let totalBytes = 0;

  // Create an array of 4 fetch promises
  const promises = Array(threadCount).fill(null).map(() => 
    fetch(`${API_URL}/download?size=${testSize}`)
      .then(res => res.body.getReader())
      .then(async reader => {
        let threadBytes = 0;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          threadBytes += value.length;
        }
        return threadBytes;
      })
  );

  // Wait for ALL threads to finish
  const results = await Promise.all(promises);
  const endTime = performance.now();
  
  // Sum up bytes from all threads
  totalBytes = results.reduce((a, b) => a + b, 0);
  
  const durationSec = (endTime - startTime) / 1000;
  
  // Calculate Mbps: (Bytes * 8) / 1,000,000 / Seconds
  return ((totalBytes * 8) / 1000000 / durationSec).toFixed(2);
};
