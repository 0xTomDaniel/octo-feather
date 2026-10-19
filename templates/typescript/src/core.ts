export interface Greeting {
  readonly name: string;
  readonly text: string;
}

export function greet(name: string): Greeting {
  const clean = name.trim();
  if (clean === "") {
    throw new Error("name must not be empty");
  }
  return { name: clean, text: `Hello, ${clean}` };
}
