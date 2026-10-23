export interface Greeting {
  name: string;
  text: string;
}

export function greet(name: any): Greeting {
  const clean = String(name).trim();
  if (!clean) {
    throw new Error("name must not be empty");
  }
  return { name: clean, text: `Hello, ${clean}` };
}
