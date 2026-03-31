/**
 * Simple Markdown renderer for agent messages.
 * Supports: **bold**, headings, tables, bullet lists, code blocks, line breaks.
 */

interface Props {
  content: string;
}

export function Markdown({ content }: Props) {
  const lines = content.split("\n");
  const elements: JSX.Element[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.startsWith("```")) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(
        <pre
          key={elements.length}
          className="bg-surface-container-high border border-outline px-4 py-3 text-xs font-mono overflow-x-auto my-2"
        >
          {codeLines.join("\n")}
        </pre>
      );
      continue;
    }

    // Table (detect | at start)
    if (line.includes("|") && line.trim().startsWith("|")) {
      const tableRows: string[] = [];
      while (i < lines.length && lines[i].includes("|")) {
        tableRows.push(lines[i]);
        i++;
      }

      const parseRow = (row: string) =>
        row
          .split("|")
          .map((c) => c.trim())
          .filter((c) => c.length > 0 && !c.match(/^[-:]+$/));

      const headerCells = parseRow(tableRows[0]);
      const isSeparator = (r: string) => r.replace(/[\s|:-]/g, "").length === 0;
      const dataStart = tableRows.length > 1 && isSeparator(tableRows[1]) ? 2 : 1;

      elements.push(
        <div key={elements.length} className="overflow-x-auto my-3">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr>
                {headerCells.map((cell, j) => (
                  <th
                    key={j}
                    className="text-left px-3 py-2 text-primary font-label font-bold uppercase tracking-widest text-[10px] border-b border-outline"
                  >
                    <InlineMarkdown text={cell} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.slice(dataStart).map((row, ri) => {
                const cells = parseRow(row);
                return (
                  <tr key={ri}>
                    {cells.map((cell, ci) => (
                      <td
                        key={ci}
                        className="px-3 py-2 border-b border-outline/30 text-on-surface"
                      >
                        <InlineMarkdown text={cell} />
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // Heading
    if (line.startsWith("### ")) {
      elements.push(
        <h4
          key={elements.length}
          className="text-xs font-label font-bold uppercase tracking-widest text-primary mt-4 mb-2"
        >
          <InlineMarkdown text={line.slice(4)} />
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h3
          key={elements.length}
          className="text-sm font-headline font-bold text-on-surface mt-4 mb-2"
        >
          <InlineMarkdown text={line.slice(3)} />
        </h3>
      );
      i++;
      continue;
    }

    // Bullet list
    if (line.match(/^[-*]\s/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^[-*]\s/)) {
        items.push(lines[i].replace(/^[-*]\s/, ""));
        i++;
      }
      elements.push(
        <ul key={elements.length} className="space-y-1 my-2 ml-1">
          {items.map((item, j) => (
            <li key={j} className="flex gap-2 text-on-surface">
              <span className="text-primary mt-1.5 text-[6px]">●</span>
              <span>
                <InlineMarkdown text={item} />
              </span>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      elements.push(<div key={elements.length} className="h-2" />);
      i++;
      continue;
    }

    // Regular paragraph
    elements.push(
      <p key={elements.length} className="text-on-surface leading-relaxed">
        <InlineMarkdown text={line} />
      </p>
    );
    i++;
  }

  return <div className="space-y-1">{elements}</div>;
}

/** Inline markdown: **bold**, `code`, _italic_ */
function InlineMarkdown({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={i} className="font-bold text-on-surface">
              {part.slice(2, -2)}
            </strong>
          );
        }
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code
              key={i}
              className="px-1.5 py-0.5 bg-surface-container-high text-primary text-[11px] font-mono"
            >
              {part.slice(1, -1)}
            </code>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
