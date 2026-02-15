/**
 * Tests for Avatar component.
 */

import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { Avatar } from "../../components/avatars/Avatar";

describe("Avatar", () => {
  it("renders an image with the correct src and alt", () => {
    const { container } = render(<Avatar src="/avatars/bot.png" name="Bot" />);
    const img = container.querySelector("img");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/avatars/bot.png");
    expect(img).toHaveAttribute("alt", "Bot");
  });

  it("defaults to medium size", () => {
    const { container } = render(<Avatar src="/a.png" name="A" />);
    expect(container.querySelector(".avatar")).toHaveClass("avatar--medium");
  });

  it("applies small size class", () => {
    const { container } = render(<Avatar src="/a.png" name="A" size="small" />);
    expect(container.querySelector(".avatar")).toHaveClass("avatar--small");
  });

  it("applies large size class", () => {
    const { container } = render(<Avatar src="/a.png" name="A" size="large" />);
    expect(container.querySelector(".avatar")).toHaveClass("avatar--large");
  });

  it("defaults to default state", () => {
    const { container } = render(<Avatar src="/a.png" name="A" />);
    expect(container.querySelector(".avatar")).toHaveClass("avatar--default");
  });

  it("applies active state with glow", () => {
    const { container } = render(
      <Avatar src="/a.png" name="A" state="active" />,
    );
    expect(container.querySelector(".avatar")).toHaveClass("avatar--active");
    expect(container.querySelector(".avatar__glow")).toBeInTheDocument();
  });

  it("applies folded state", () => {
    const { container } = render(
      <Avatar src="/a.png" name="A" state="folded" />,
    );
    expect(container.querySelector(".avatar")).toHaveClass("avatar--folded");
  });

  it("applies all-in state", () => {
    const { container } = render(
      <Avatar src="/a.png" name="A" state="all-in" />,
    );
    expect(container.querySelector(".avatar")).toHaveClass("avatar--all-in");
  });

  it("applies eliminated state", () => {
    const { container } = render(
      <Avatar src="/a.png" name="A" state="eliminated" />,
    );
    expect(container.querySelector(".avatar")).toHaveClass(
      "avatar--eliminated",
    );
  });

  it("does not render glow when not active", () => {
    const { container } = render(
      <Avatar src="/a.png" name="A" state="folded" />,
    );
    expect(container.querySelector(".avatar__glow")).not.toBeInTheDocument();
  });
});
