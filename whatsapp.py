"""Program to visualize WhatsApp data."""

# import dependencies
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import sys
import re
import datetime
import logging

from nltk import sent_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer

matplotlib.style.use('ggplot')  # select matplotlib style
logging.basicConfig(level=logging.INFO)


class Visualizer():
    """Base visualizer class."""

    def __init__(self):
        """Initialize class."""
        self.filename, self.users = self.set_consts()
        self.data = self.get_dataframe()
        self.colors = ['red', 'blue', 'yellow', 'green', 'purple',
                       'black', 'pink', 'cyan', 'orange']
        self.twelve_format = False

    def set_consts(self, filename='whatsapp.txt'):
        """Set user and filename constants."""
        with open(filename, 'r', encoding='utf-8') as f:
            users_re = re.findall('\d{2}:\d{2}(?: AM|PM)? - (?P<users>.+?): ', f.read())
            if not users_re:
                raise Exception('Users not detected. Aborting program')
            users = list(set(users_re))

        if len(sys.argv) > 1:   # if command line arguments are greater than one
            filename = sys.argv[1]   # set filename to first command line argument after python script's name
        else:
            filename = filename

        return filename, users

    def get_dataframe(self):
        """Return dataframe with all the data from txt file."""

        def format_times(time, format):
            format = format[1:]
            if format == "AM":
                if len(time) == 4:
                    return '0' + time
                if len(time) == 5:
                    return time

            if format == "PM":
                hrs = time.split(':')[0]
                mins = time.split(':')[1]
                hrs = str(int(hrs) + 12)
                return "{}:{}".format(hrs, mins)

        reg = '|'.join(self.users)

        # get messages into dataframe
        with open(self.filename, 'r', encoding='utf-8') as f:
            line_reg_obj = re.compile(r'(\d+/\d+/\d{{2}}), (\d\d:\d\d)(\sAM|PM)?\s-\s({}):\s(.*)'.format(reg))   # create regular expression to separate the messages' components
            info = line_reg_obj.findall(f.read())  # find all matches for regular expression
            data = pd.DataFrame(info, columns=['Date', 'Time', 'Format', 'Sender', 'Message'])  # create dataframe

        # if data['Format'].unique():
        #     data['Time'] = data.apply(lambda x: format_times(x['Time'], x['Format']), axis=1)
        #
        # data = data.drop(columns='Format')

        return data

    def get_plot_data(self, date_or_time):
        """Return dataframe with sender, frequency, and date/time information."""
        data = self.data
        plot_data = pd.DataFrame(columns=[date_or_time, 'Sender', 'Frequency'])  # create dataframe to be populated

        for sender in data['Sender'].unique():  # populate information for each unique sender
            a = dict(data[data['Sender'] == sender].groupby(data[date_or_time]).count()[date_or_time])  # creates dictionary of series obtained
            b = pd.DataFrame(columns=[date_or_time, 'Sender', 'Frequency'])  # create temporary dataframe to append values to plot_data
            b[date_or_time] = a.keys()  # append date_or_time values to b
            b['Frequency'] = a.values()  # append frequency values to b
            b['Sender'] = sender  # append sender information to b
            plot_data = pd.concat([plot_data, b])  # append b to plot_data

        # if function implemented to allow code reuse in function
        if date_or_time == 'Time':
            op1 = lambda x: datetime.datetime.strptime(x, '%H:%M')  # create lambda function to convert time values to datetime object
        elif date_or_time == 'Date':
            op1 = lambda x: datetime.datetime.strptime(x, '%m/%d/%y')  # create lambda function to convert date values to datetime object
        op2 = lambda x: matplotlib.dates.date2num(x)   # create lambda function to convert date_or_time values to matplotlib date object

        plot_data[date_or_time] = plot_data[date_or_time].apply(op1)  # apply lambda function 1
        plot_data[date_or_time] = plot_data[date_or_time].apply(op2)  # apply lambda function 2

        return plot_data

    def set_title_and_legend(self, ax, x_axis):
        """Set title, labels, and legend for graph where function is called."""
        ax.set_title('Graph of Frequency against ' + x_axis)  # set x-axis title
        ax.set_xlabel(x_axis)  # set x-axis label
        ax.set_ylabel('Frequency')  # set y-axis label

        ax.legend()  # set legend

    def time_scatter_plot(self):
        """Create scatter plot of time against frequency from data dataframe."""
        x_axis = 'Time'  # set x-axis lable and value

        plot_data = self.get_plot_data(x_axis)  # get data to be plotted

        fig = plt.figure(figsize=(16, 8))  # create figure
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])  # set axes

        for sender, color in zip(plot_data['Sender'].unique(), self.colors):
            ax.scatter(x=x_axis, y='Frequency', data=plot_data[plot_data['Sender'] == sender], c=color, label=sender)  # plot scatterplot for each unique sender

        ax.xaxis_date()  # inform graph that dates will be plotted on the x-axis
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))  # format x-axis values

        self.set_title_and_legend(ax, x_axis)  # set title, labels, and legends
        fig.savefig(x_axis)  # export graph as .png file

    def date_line_plot(self):
        """Create line graph of date against frequency from data dataframe."""
        x_axis = 'Date'  # set x-axis lable and value

        plot_data = self.get_plot_data(x_axis)  # get data to be plotted
        plot_data.sort_values(x_axis, inplace=True)  # sort date values to create smooth line graph

        fig = plt.figure(figsize=(16, 8))  # create figure
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])  # set axes

        for sender, color in zip(plot_data['Sender'].unique(), self.colors):
            temp = plot_data[plot_data['Sender'] == sender]
            ax.plot(temp[x_axis], temp['Frequency'], c=color, label=sender)  # plot line graph for each unique sender

        ax.xaxis_date()  # inform graph that dates will be plotted on the x-axis
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d-%m-%y'))  # format x-axis date values
        fig.autofmt_xdate()  # beautify x-axis values

        self.set_title_and_legend(ax, x_axis)  # set title, labels, and legends
        fig.savefig(x_axis)  # export graph as .png file

    def get_sentiment_data(self, date_or_time):

        def format_datetimes(x, date_or_time):
            if date_or_time == "Date":
                x = datetime.datetime.strptime(x, '%m/%d/%y')
            if date_or_time == "Time":
                x = datetime.datetime.strptime(x, '%H:%M')
            return matplotlib.dates.date2num(x)

        sent_data = pd.DataFrame(columns=['Sender', date_or_time, 'Score'])
        analyzer = SentimentIntensityAnalyzer()

        for sender, color in zip(self.data['Sender'].unique(), self.colors):
            for period in self.data[date_or_time].unique():
                temp_df = self.data.loc[(self.data['Sender'] == sender) &
                                        (self.data[date_or_time] == period)]
                period_scores = []
                for message in temp_df['Message']:
                    if message == "<Media omitted>":
                        continue
                    sentences = sent_tokenize(message)
                    message_scores = []
                    for sentence in sentences:
                        scores = analyzer.polarity_scores(sentence)
                        message_scores.append(scores['compound'])
                    message_score = sum(message_scores)/len(message_scores)
                    period_scores.append(message_score)
                try:
                    period_score = sum(period_scores)/len(period_scores)
                    row = {'Sender': sender, date_or_time: period, 'Score': period_score}
                    sent_data = sent_data.append(row, ignore_index=True)
                except ZeroDivisionError:
                    pass

        sent_data[date_or_time] = sent_data[date_or_time].apply(
                                                           format_datetimes,
                                                           date_or_time=date_or_time)

        return sent_data

    def set_sent_title_and_legend(self, ax, date_or_time):
        """Set title, labels, and legend for graph where function is called."""
        ax.set_title('Graph of Sentiment against ' + date_or_time)  # set x-axis title
        ax.set_xlabel(date_or_time)  # set x-axis label
        ax.set_ylabel('Sentiment')  # set y-axis label

        ax.legend()  # set legend

    def plot_sentiment_data(self):

        def set_flags(date_or_time, date=False, time=False):
            if date_or_time == "Date":
                date = True
            if date_or_time == "Time":
                time = True
            return date, time

        for date_or_time in ('Date', 'Time'):
            date, time = set_flags(date_or_time)

            sent_plot_data = self.get_sentiment_data(date_or_time)

            if date:
                sent_plot_data.sort_values(date_or_time, inplace=True)  # sort date values to create smooth line graph

            fig = plt.figure(figsize=(16, 8))  # create figure
            ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])  # set axes

            for sender, color in zip(sent_plot_data['Sender'].unique(),
                                     self.colors):
                if date:
                    temp = sent_plot_data[sent_plot_data['Sender'] == sender]
                    ax.plot(temp[date_or_time], temp['Score'],
                            c=color, label=sender)  # plot line graph for each unique sender
                if time:
                    ax.scatter(x=date_or_time, y='Score',
                               data=sent_plot_data[sent_plot_data['Sender'] == sender],
                               c=color, label=sender)  # plot scatterplot for each unique sender

            ax.xaxis_date()  # inform graph that dates will be plotted on the x-axis

            if date:
                ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter
                                             ('%d-%m-%y'))  # format x-axis date values
            if time:
                ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter
                                             ('%H:%M'))  # format x-axis values

            fig.autofmt_xdate()  # beautify x-axis values

            self.set_sent_title_and_legend(ax, date_or_time)  # set title, labels, and legends
            fig.savefig("{}_Sentiment".format(date_or_time))  # export graph as .png file

        logging.info("Graphs have been created.")


if __name__ == "__main__":
    program = Visualizer()
    program.time_scatter_plot()
    program.date_line_plot()
    program.plot_sentiment_data()
