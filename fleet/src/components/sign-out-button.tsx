import { Button } from "@/components/ui";

export function SignOutButton({ className = "" }: { className?: string }) {
  return (
    <form action="/auth/signout" method="post" className={className}>
      <Button type="submit" variant="secondary" className="w-full">
        Odhlásiť sa
      </Button>
    </form>
  );
}
