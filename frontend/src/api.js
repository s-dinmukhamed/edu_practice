export async function detectImage(apiUrl, file, conf) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${apiUrl}/detect?conf=${conf}`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      msg = err.detail || msg;
    } catch {}
    throw new Error(msg);
  }

  return res.json();
}
