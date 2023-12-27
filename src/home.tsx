import cx from "classnames";
import { scaleLinear } from "d3-scale";
import * as AR from "fp-ts/Array";
import * as O from "fp-ts/Option";
import { pipe } from "fp-ts/function";
import { contramap } from "fp-ts/lib/Ord";
import * as N from "fp-ts/number";
import { useMemo, useState } from "react";
import eval_result from "../scripts/eval_result.json";
import { ms } from "../utils/functions";

const categories = {
  all: 8000,
  "american indian/alaska native foods": 165,
  "baby foods": 367,
  "baked products": 879,
  "beef products": 961,
  beverages: 371,
  "breakfast cereals": 356,
  "cereal grains and pasta": 181,
  "dairy and egg products": 283,
  "fast foods": 363,
  "fats and oils": 220,
  "finfish and shellfish products": 265,
  "fruits and fruit juices": 360,
  "lamb, veal, and game products": 464,
  "legumes and legume products": 381,
  "meals, entrees, and side dishes": 125,
  "nut and seed products": 137,
  "pork products": 341,
  "poultry products": 389,
  "restaurant foods": 109,
  "sausages and luncheon meats": 170,
  snacks: 177,
  "soups, sauces, and gravies": 465,
  "spices and herbs": 64,
  sweets: 360,
  "vegetables and vegetable products": 836,
};

interface Food {
  true: number;
  predicted: number;
  error: number;
}

type Macro = "calories" | "proteins" | "fats" | "carbohydrates";

const byError = pipe(
  N.Ord,
  contramap((food: Food) => food.error)
);

function Home() {
  const [selectedValue, setSelectedValue] = useState<O.Option<any>>(O.none);
  const [macro, setMacro] = useState<Macro>("calories");
  const [selectedCategory, setSelectedCategory] = useState<any>("all");

  const values = useMemo(
    () =>
      pipe(
        eval_result,
        AR.map((food) => ({
          true: food.nutrients[macro],
          predicted: food.estimated_nutrients[macro],
          error: food.estimated_nutrients[macro] - food.nutrients[macro],
          description: food.item_description,
        })),
        AR.sortBy([byError])
      ),
    [eval_result, macro]
  );

  const valueToPosition = useMemo(
    () =>
      scaleLinear()
        .domain([
          Math.min(
            ...values.map((value) => value.true),
            ...values.map((value) => value.predicted)
          ),
          Math.max(
            ...values.map((value) => value.true),
            ...values.map((value) => value.predicted)
          ),
        ])
        .range([0, ms(12)]),
    [values]
  );

  return (
    <div className="page">
      <div className="categories">
        {Object.keys(categories).map((category) => (
          <div
            key={category}
            className={cx("category", {
              selected: category === selectedCategory,
            })}
            onClick={() => {
              setSelectedCategory(category);
            }}
          >
            {category}
          </div>
        ))}
      </div>

      <div className="workspace">
        <div className="tabs">
          {["calories", "carbohydrates", "proteins", "fats"].map((tab: any) => (
            <div
              className={cx("tab", { ["selected"]: tab === macro })}
              onClick={() => {
                setMacro(tab);
              }}
            >
              {tab}
            </div>
          ))}
        </div>

        <div className="values">
          {values.map((value, index) => (
            <div
              key={index}
              className="value"
              onMouseEnter={() => {
                setSelectedValue(O.some(value));
              }}
              onMouseLeave={() => {
                setSelectedValue(O.none);
              }}
            >
              <div
                className="dot true"
                style={{ bottom: valueToPosition(value.true) }}
              />
              <div
                className="dot predicted"
                style={{ bottom: valueToPosition(value.predicted) }}
              />
              <div
                className="error"
                style={{
                  bottom:
                    valueToPosition(Math.min(value.predicted, value.true)) +
                    ms(-5) / 2,
                  height: Math.abs(
                    valueToPosition(value.true) -
                      valueToPosition(value.predicted)
                  ),
                }}
              />
            </div>
          ))}
        </div>

        {O.isSome(selectedValue) && (
          <div className="quicklook">
            <div>{selectedValue.value.description}</div>
            <div>{selectedValue.value.error.toFixed(2)}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Home;
