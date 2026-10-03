import LoginForm from "@/components/LoginForm";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ expired?: string }>;
}) {
  const { expired } = await searchParams;
  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <LoginForm sessionExpired={expired === "1"} />
    </main>
  );
}