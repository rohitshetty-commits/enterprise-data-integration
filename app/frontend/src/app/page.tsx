import { apiGet } from "@/lib/api";

type HelloResponse = { message: string };

export default async function Home() {
  let message = "Loading...";
  let error: string | null = null;

  try {
    const data = await apiGet<HelloResponse>("/api/v1/hello");
    message = data.message;
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to reach backend";
    message = "";
  }

  return (
    <main style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Interface — App Frontend</h1>
      <p>Next.js frontend scaffold for the app builder agents.</p>
      {error ? (
        <p style={{ color: "crimson" }}>Error: {error}</p>
      ) : (
        <p><strong>Backend says:</strong> {message}</p>
      )}
    </main>
  );
}
