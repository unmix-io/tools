using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;

namespace AudioQualityAssuranceTool
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        public App()
        {
            var currentDomain = AppDomain.CurrentDomain;
            currentDomain.UnhandledException += new UnhandledExceptionEventHandler(ExceptionHandler);
        }
        void App_DispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            // Process unhandled exception
            ExceptionHandler(sender, new UnhandledExceptionEventArgs(e.Exception, true));
            // Prevent default unhandled exception processing
            e.Handled = true;
        }

        static void ExceptionHandler(object sender, UnhandledExceptionEventArgs args)
        {
            var e = (Exception)args.ExceptionObject;
            var message = $"Exception: {e.GetType().Name}{Environment.NewLine}"
                          + $"Message: {e.Message}{Environment.NewLine}"
                          + $"InnerException: {e.InnerException?.GetType()}{Environment.NewLine}"
                          + $"Message: {e.InnerException?.Message}{Environment.NewLine}"
                          + $"StackTrace: {e.StackTrace}{Environment.NewLine}";
            MessageBox.Show(message, "Exception");
        }
    }
}
