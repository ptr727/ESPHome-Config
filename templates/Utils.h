// https://github.com/esphome/esphome/blob/release/esphome/components/display/display.h
class DisplayHelper
{
    public:

        // Return the height of the font in pixels
        static int GetFontHeightInPixels(esphome::display::Display* pDisplay, esphome::font::Font *pFont)
        {
            int x = 0, y = 0, width = 0, height = 0;
            pDisplay->get_text_bounds(0, 0, "A!%", pFont, TextAlign::TOP_LEFT, &x, &y, &width, &height);
            return height;
        }

        // Return the line spacing in pixels for vertically equal distribution of lines
        struct LineSpacing
        {
            int nFirstLine;
            int nIncrement;
        };
        static LineSpacing GetLineSpacing(esphome::display::Display* pDisplay, esphome::font::Font *pFont, int nNumLines)
        {
            LineSpacing lineSpacing;
            lineSpacing.nIncrement = pDisplay->get_height() / (nNumLines + 1);
            lineSpacing.nFirstLine = lineSpacing.nIncrement - (GetFontHeightInPixels(pDisplay, pFont) / 2);
            return lineSpacing;
        }
};

// Refer to Norvi docs for resistor ladder values:
// https://norvi.lk/docs/norvi-enet-ae06-r-norvi-enet-ae06-r-user-guide/
// 3.3V, S3, 10K, 47K, GND
// 3.3V, S2, 33K, 47K, GND
// 3.3V, S1, 67K, 47K, GND
// Rbutton = 1 / (1/R2 + 1/R3 + 1/R4)
// Vbutton = (Vin x R6) / (Rbutton + R6)
// S3 | S2 | S1 | Rbutton     | Vbutton     | Delta       | % of 3.3v
// 0  | 0  | 0  | ∞           | 0           |             |
// 0  | 0  | 1  | 67000       | 1.360526316 | 1.360526316 | 41.22807018
// 0  | 1  | 0  | 33000       | 1.93875     | 0.578223684 | 17.52192982
// 0  | 1  | 1  | 22110       | 2.2442483   | 0.3054983   | 9.257524237
// 1  | 0  | 0  | 10000       | 2.721052632 | 0.476804332 | 14.44861611
// 1  | 0  | 1  | 8701.298701 | 2.78449522  | 0.063442589 | 1.922502689
// 1  | 1  | 0  | 7674.418605 | 2.836792854 | 0.052297634 | 1.584776781
// 1  | 1  | 1  | 6885.705388 | 2.878314367 | 0.041521513 | 1.258227667
// TODO: https://github.com/espressif/esp-adf/blob/master/components/esp_peripherals/lib/adc_button/adc_button.c
class NorviButtonHelper
{
public:

    static void GetMultiButtonState(double adc, bool& s1, bool& s2, bool& s3)
    {
        s1 = false;
        s2 = false;
        s3 = false;

        // Singleton
        static ButtonValue* buttonValues = nullptr;
        if (buttonValues == nullptr)
        {
           buttonValues = CalculateButtonValues();
        }

        // Window needs to be less than half of smallest delta between voltages
        // Smallest delta is 0.041521513
        static constexpr double VWindow = 0.02;

        // Test all combinations of button press values
        for (int i = 1; i < Count; i++)
        {
            // Match ADC voltage in window
            if (adc >= buttonValues[i].Volt - VWindow && adc <= buttonValues[i].Volt + VWindow)
            {
                s3 = buttonValues[i].S3;
                s2 = buttonValues[i].S2;
                s1 = buttonValues[i].S1;
                break;
            }
        }
    }

    static void GetSingleButtonState(double adc, bool& s1, bool& s2, bool& s3)
    {
        s1 = false;
        s2 = false;
        s3 = false;

        // Singleton
        static ButtonValue* buttonValues = nullptr;
        if (buttonValues == nullptr)
        {
           buttonValues = CalculateButtonValues();
        }

        // Window needs to be less than half of smallest delta between voltages
        // Smallest delta is 0.578223684
        static constexpr double VWindow = 0.25;

        // Test individual button press values
        for (int i = 1; i < Count; i <<= 1)
        {
            // Match ADC voltage in window
            if (adc >= buttonValues[i].Volt - VWindow && adc <= buttonValues[i].Volt + VWindow)
            {
                s3 = buttonValues[i].S3;
                s2 = buttonValues[i].S2;
                s1 = buttonValues[i].S1;
                break;
            }
        }
    }

    static void LogButtonValues()
    {
        ButtonValue* buttonValues = CalculateButtonValues();
        for (int i = 0; i < Count; i++)
        {
            ESP_LOGI("NorviButtonHelper", "S3: %d, S2: %d, S1: %d, V: %f", buttonValues[i].S3, buttonValues[i].S2, buttonValues[i].S1, buttonValues[i].Volt);
            // std::cout << "NorviButtonHelper: Index: " << i << " S3: " << buttonValues[i].S3 << " S2: " << buttonValues[i].S2 << " S1: " << buttonValues[i].S1 << " V: " << buttonValues[i].Volt << std::endl;
        }
    }

private:

    static constexpr double VRef = 3.3;
    static const int R2 = 10000;
    static const int R3 = 33000;
    static const int R4 = 67000;
    static const int R6 = 47000;
    static const int Count = 8;

    struct ButtonValue
    {
        bool S3;
        bool S2;
        bool S1;
        double Volt;
    };

    static double GetRButton(bool S3, bool S2, bool S1)
    {
        return 1.0 / (int(S3) * 1.0 / R2 + int(S2) * 1.0 / R3 + int(S1) * 1.0 / R4);
    }

    static double GetVButton(bool S3, bool S2, bool S1)
    {
        if (S3 == false && S2 == false && S1 == false)
        {
            // Avoid div by 0
            return 0.0;
        }
        return (VRef * R6) / (GetRButton(S3, S2, S1) + R6);
    }

    static ButtonValue* CalculateButtonValues()
    {
        // 3 bits for 8 combinations of button presses
        ButtonValue *buttonValues = new ButtonValue[Count];
        for (int i = 0; i < Count; i++)
        {
            buttonValues[i].S3 = bool((i >> 0) & 1);
            buttonValues[i].S2 = bool((i >> 1) & 1);
            buttonValues[i].S1 = bool((i >> 2) & 1);
            buttonValues[i].Volt = GetVButton(buttonValues[i].S3, buttonValues[i].S2, buttonValues[i].S1);
        }
        return buttonValues;
    }

    // Need C++ 17+ for inline in header
    // static inline ButtonValue* ButtonValues = NorviButtonHelper::CalculateButtonValues();
};
