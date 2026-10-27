/**
 * The TOML the app-driver contract (qc.toml) is written in: tables, dotted and quoted keys, strings
 * (basic, literal, multi-line), integers and booleans. Anything else (arrays, inline tables, floats,
 * dates) is refused naming its line, never guessed at; the contract's schema uses none of them.
 *
 * Why not a TOML package: the helper reads qc.toml before it runs the contract's setup, the step that
 * installs this repo's packages, so it can rely on nothing but Node itself.
 */

export type TomlValue = string | number | boolean | TomlTable;
export interface TomlTable {
  [key: string]: TomlValue;
}

export class TomlError extends Error {}

const BARE = /[A-Za-z0-9_-]/;
const ESCAPES: Record<string, string> = { b: "\b", t: "\t", n: "\n", f: "\f", r: "\r", '"': '"', "\\": "\\" };

export function parseToml(text: string): TomlTable {
  return new Reader(text).document();
}

function isTable(v: TomlValue | undefined): v is TomlTable {
  return typeof v === "object";
}

class Reader {
  private pos = 0;
  private readonly root: TomlTable = {};
  private readonly defined = new Set<TomlTable>();
  private readonly src: string;

  constructor(src: string) {
    this.src = src;
  }

  document(): TomlTable {
    let table = this.root;
    for (;;) {
      this.skipBlankLines();
      if (this.pos >= this.src.length) return this.root;
      if (this.src.startsWith("[[", this.pos)) this.fail("arrays of tables are not read here");
      if (this.peek() === "[") {
        this.pos++;
        table = this.header(this.keyPath());
        this.inlineSpace();
        this.expect("]");
      } else {
        this.keyValue(table);
      }
      this.endOfLine();
    }
  }

  private header(path: string[]): TomlTable {
    let t = this.root;
    for (const k of path) {
      const next = t[k] ?? {};
      if (!isTable(next)) this.fail(`${path.join(".")}: ${k} is already a value`);
      t[k] = next;
      t = next;
    }
    if (this.defined.has(t)) this.fail(`table [${path.join(".")}] defined twice`);
    this.defined.add(t);
    return t;
  }

  private keyValue(table: TomlTable): void {
    const path = this.keyPath();
    this.inlineSpace();
    this.expect("=");
    this.inlineSpace();
    const value = this.value();
    let t = table;
    for (const k of path.slice(0, -1)) {
      const next = t[k] ?? {};
      if (!isTable(next)) this.fail(`${path.join(".")}: ${k} is already a value`);
      t[k] = next;
      t = next;
    }
    const last = path.at(-1) ?? "";
    if (last in t) this.fail(`key ${path.join(".")} defined twice`);
    t[last] = value;
  }

  private keyPath(): string[] {
    const path: string[] = [];
    for (;;) {
      this.inlineSpace();
      const c = this.peek();
      if (c === '"') path.push(this.basicString());
      else if (c === "'") path.push(this.literalString());
      else {
        const start = this.pos;
        while (BARE.test(this.peek())) this.pos++;
        if (start === this.pos) this.fail("expected a key");
        path.push(this.src.slice(start, this.pos));
      }
      this.inlineSpace();
      if (this.peek() !== ".") return path;
      this.pos++;
    }
  }

  private value(): TomlValue {
    if (this.src.startsWith('"""', this.pos)) return this.multiline('"""');
    if (this.src.startsWith("'''", this.pos)) return this.multiline("'''");
    const c = this.peek();
    if (c === '"') return this.basicString();
    if (c === "'") return this.literalString();
    const word = /^[^\s#,\]}]+/.exec(this.src.slice(this.pos))?.[0] ?? "";
    this.pos += word.length;
    if (word === "true") return true;
    if (word === "false") return false;
    if (/^[+-]?(0|[1-9](_?[0-9])*)$/.test(word)) return Number(word.replaceAll("_", ""));
    return this.fail(`unsupported value ${JSON.stringify(word || c)}: this reader takes strings, integers and booleans`);
  }

  private basicString(): string {
    this.expect('"');
    let out = "";
    for (;;) {
      const c = this.peek();
      if (c === "" || c === "\n") this.fail("unterminated string");
      this.pos++;
      if (c === '"') return out;
      out += c === "\\" ? this.escape() : c;
    }
  }

  private escape(): string {
    const c = this.peek();
    this.pos++;
    const simple = ESCAPES[c];
    if (simple !== undefined) return simple;
    const width = c === "u" ? 4 : c === "U" ? 8 : 0;
    const hex = this.src.slice(this.pos, this.pos + width);
    if (width === 0 || !/^[0-9A-Fa-f]+$/.test(hex) || hex.length !== width) this.fail(`bad escape \\${c}`);
    this.pos += width;
    return String.fromCodePoint(parseInt(hex, 16));
  }

  private literalString(): string {
    this.expect("'");
    const end = this.src.indexOf("'", this.pos);
    const newline = this.src.indexOf("\n", this.pos);
    if (end === -1 || (newline !== -1 && newline < end)) this.fail("unterminated string");
    const out = this.src.slice(this.pos, end);
    this.pos = end + 1;
    return out;
  }

  private multiline(quote: '"""' | "'''"): string {
    this.pos += 3;
    if (this.peek() === "\n") this.pos++;
    else if (this.src.startsWith("\r\n", this.pos)) this.pos += 2;
    let out = "";
    for (;;) {
      if (this.pos >= this.src.length) this.fail("unterminated multi-line string");
      if (this.src.startsWith(quote, this.pos)) {
        this.pos += 3;
        // Up to two quotes right after the closing three belong to the string.
        const q = quote.charAt(0);
        for (let extra = 0; extra < 2 && this.peek() === q; extra++) {
          out += q;
          this.pos++;
        }
        return out;
      }
      const c = this.peek();
      this.pos++;
      if (quote === '"""' && c === "\\") {
        if (/^[ \t]*\r?\n/.test(this.src.slice(this.pos))) {
          // A line-ending backslash trims the newline and the whitespace that follows.
          while (/\s/.test(this.peek())) this.pos++;
        } else {
          out += this.escape();
        }
      } else {
        out += c;
      }
    }
  }

  private skipBlankLines(): void {
    for (;;) {
      this.inlineSpace();
      if (this.peek() === "#") this.comment();
      if (this.peek() === "\n") this.pos++;
      else if (this.src.startsWith("\r\n", this.pos)) this.pos += 2;
      else return;
    }
  }

  private endOfLine(): void {
    this.inlineSpace();
    if (this.peek() === "#") this.comment();
    if (this.peek() === "\n") this.pos++;
    else if (this.src.startsWith("\r\n", this.pos)) this.pos += 2;
    else if (this.pos < this.src.length) this.fail("expected the end of the line");
  }

  private comment(): void {
    while (this.pos < this.src.length && this.peek() !== "\n") this.pos++;
  }

  private inlineSpace(): void {
    while (this.peek() === " " || this.peek() === "\t") this.pos++;
  }

  private expect(c: string): void {
    if (this.peek() !== c) this.fail(`expected ${c}`);
    this.pos++;
  }

  private peek(): string {
    return this.src[this.pos] ?? "";
  }

  private fail(why: string): never {
    const line = this.src.slice(0, this.pos).split("\n").length;
    throw new TomlError(`line ${String(line)}: ${why}`);
  }
}
