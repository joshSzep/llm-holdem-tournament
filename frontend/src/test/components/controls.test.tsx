/**
 * Tests for ActionButtons, RaiseSlider, and PresetButtons.
 */

import { render, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ActionButtons } from "../../components/controls/ActionButtons";
import { RaiseSlider } from "../../components/controls/RaiseSlider";
import { PresetButtons } from "../../components/controls/PresetButtons";

// ─── ActionButtons ───────────────────────────────────

describe("ActionButtons", () => {
  const defaultProps = {
    canCheck: false,
    canCall: false,
    canRaise: false,
    callAmount: 0,
    minRaise: 20,
    maxRaise: 1000,
    potSize: 100,
    bigBlind: 20,
    onFold: vi.fn(),
    onCheck: vi.fn(),
    onCall: vi.fn(),
    onRaise: vi.fn(),
  };

  it("always renders fold button", () => {
    const { container } = render(<ActionButtons {...defaultProps} />);
    expect(
      container.querySelector(".action-buttons__btn--fold"),
    ).toBeInTheDocument();
  });

  it("renders check button when canCheck", () => {
    const { container } = render(
      <ActionButtons {...defaultProps} canCheck />,
    );
    expect(
      container.querySelector(".action-buttons__btn--check"),
    ).toHaveTextContent("Check");
  });

  it("does not render check button when canCheck is false", () => {
    const { container } = render(<ActionButtons {...defaultProps} />);
    expect(
      container.querySelector(".action-buttons__btn--check"),
    ).not.toBeInTheDocument();
  });

  it("renders call button with amount when canCall", () => {
    const { container } = render(
      <ActionButtons {...defaultProps} canCall callAmount={50} />,
    );
    const btn = container.querySelector(".action-buttons__btn--call");
    expect(btn).toHaveTextContent("Call 50");
  });

  it("renders raise controls when canRaise", () => {
    const { container } = render(
      <ActionButtons {...defaultProps} canRaise />,
    );
    expect(
      container.querySelector(".action-buttons__raise-controls"),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".action-buttons__btn--raise"),
    ).toBeInTheDocument();
  });

  it("does not render raise controls when canRaise is false", () => {
    const { container } = render(<ActionButtons {...defaultProps} />);
    expect(
      container.querySelector(".action-buttons__raise-controls"),
    ).not.toBeInTheDocument();
  });

  it("calls onFold when fold button clicked", () => {
    const onFold = vi.fn();
    const { container } = render(
      <ActionButtons {...defaultProps} onFold={onFold} />,
    );
    fireEvent.click(container.querySelector(".action-buttons__btn--fold")!);
    expect(onFold).toHaveBeenCalledOnce();
  });

  it("calls onCheck when check button clicked", () => {
    const onCheck = vi.fn();
    const { container } = render(
      <ActionButtons {...defaultProps} canCheck onCheck={onCheck} />,
    );
    fireEvent.click(container.querySelector(".action-buttons__btn--check")!);
    expect(onCheck).toHaveBeenCalledOnce();
  });

  it("calls onCall when call button clicked", () => {
    const onCall = vi.fn();
    const { container } = render(
      <ActionButtons {...defaultProps} canCall callAmount={100} onCall={onCall} />,
    );
    fireEvent.click(container.querySelector(".action-buttons__btn--call")!);
    expect(onCall).toHaveBeenCalledOnce();
  });
});

// ─── RaiseSlider ─────────────────────────────────────

describe("RaiseSlider", () => {
  it("renders slider and input", () => {
    const { container } = render(
      <RaiseSlider
        minRaise={20}
        maxRaise={1000}
        currentAmount={100}
        onAmountChange={vi.fn()}
      />,
    );
    expect(container.querySelector(".raise-slider__range")).toBeInTheDocument();
    expect(container.querySelector(".raise-slider__input")).toBeInTheDocument();
  });

  it("updates amount on slider change", () => {
    const onChange = vi.fn();
    const { container } = render(
      <RaiseSlider
        minRaise={20}
        maxRaise={1000}
        currentAmount={100}
        onAmountChange={onChange}
      />,
    );
    const slider = container.querySelector(
      ".raise-slider__range",
    ) as HTMLInputElement;
    fireEvent.change(slider, { target: { value: "500" } });
    expect(onChange).toHaveBeenCalledWith(500);
  });

  it("displays current amount in input", () => {
    const { container } = render(
      <RaiseSlider
        minRaise={20}
        maxRaise={1000}
        currentAmount={250}
        onAmountChange={vi.fn()}
      />,
    );
    const input = container.querySelector(
      ".raise-slider__input",
    ) as HTMLInputElement;
    expect(input.value).toBe("250");
  });

  it("clamps invalid input on blur", () => {
    const onChange = vi.fn();
    const { container } = render(
      <RaiseSlider
        minRaise={20}
        maxRaise={1000}
        currentAmount={100}
        onAmountChange={onChange}
      />,
    );
    const input = container.querySelector(
      ".raise-slider__input",
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "5" } });
    fireEvent.blur(input);
    expect(onChange).toHaveBeenCalledWith(20); // clamped to min
  });
});

// ─── PresetButtons ───────────────────────────────────

describe("PresetButtons", () => {
  const defaultProps = {
    minRaise: 20,
    maxRaise: 1000,
    potSize: 200,
    bigBlind: 20,
    onSelect: vi.fn(),
  };

  it("renders all preset buttons", () => {
    const { container } = render(<PresetButtons {...defaultProps} />);
    const buttons = container.querySelectorAll(".preset-buttons__btn");
    expect(buttons).toHaveLength(5);
  });

  it("calls onSelect with min raise for Min button", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <PresetButtons {...defaultProps} onSelect={onSelect} />,
    );
    const buttons = container.querySelectorAll(".preset-buttons__btn");
    fireEvent.click(buttons[0]!);
    expect(onSelect).toHaveBeenCalledWith(20);
  });

  it("calls onSelect with max raise for All-In button", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <PresetButtons {...defaultProps} onSelect={onSelect} />,
    );
    const buttons = container.querySelectorAll(".preset-buttons__btn");
    fireEvent.click(buttons[4]!);
    expect(onSelect).toHaveBeenCalledWith(1000);
  });

  it("calls onSelect with pot size for Pot button", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <PresetButtons {...defaultProps} onSelect={onSelect} />,
    );
    const buttons = container.querySelectorAll(".preset-buttons__btn");
    fireEvent.click(buttons[3]!);
    expect(onSelect).toHaveBeenCalledWith(200);
  });

  it("disables buttons when min > max", () => {
    const { container } = render(
      <PresetButtons {...defaultProps} minRaise={1000} maxRaise={500} />,
    );
    const buttons = container.querySelectorAll(".preset-buttons__btn");
    for (const btn of buttons) {
      expect(btn).toBeDisabled();
    }
  });
});
