# Load necessary libraries
library(ggplot2)
library(dplyr)

options(echo=TRUE)
args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 1) {
  stop("Please provide the path to one CSV file.")
}
# Read the CSV file
data <- read.csv(args[1])
# Normalize the unix_timestamp
data <- data %>%
  mutate(normalized_timestamp = unix_timestamp - min(unix_timestamp))

# Plot the data using ggplot2
ggplot(data, aes(x = normalized_timestamp, y = cwnd)) +
  geom_line() +
  geom_point() +
  labs(title = "CWND over Time",
       x = "Time (seconds)",
       y = "CWND (bytes)") +
  theme_minimal()
