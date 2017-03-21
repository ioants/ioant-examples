# Body weight scale device
Device that measures the pulse width of a pwm signal sent from an older body weight scale. Using a linear approximation the body-weight scale attempts to derive the weight in kilograms and then publish it as a mass-stream


```sh
# To build the project. Available environments: esp01, esp12e
pio run -e es12e
```

```sh
# To build and upload the project. Available environments: esp01, esp12e
pio run -e es12e -t upload
```
