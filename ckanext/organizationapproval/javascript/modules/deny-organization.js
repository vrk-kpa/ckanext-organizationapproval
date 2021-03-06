'use strict';

ckan.module('deny-organization', function(jQuery) {
    return {
        /* An object of module options */
        options: {
            /* Content can be overriden by setting data-module-content to a
             * *translated* string inside the template, e.g.
             *
             *     <a href="..."
             *        data-module="confirm-action"
             *        data-module-content="{{ _('Are you sure?') }}">
             *    {{ _('Delete') }}
             *    </a>
             */
            content: '',
            placeholder: '',

            /* This is part of the old i18n system and is kept for backwards-
             * compatibility for templates which set the content via the
             * `i18n.content` attribute instead of via the `content` attribute
             * as described above.
             */
            i18n: {
                content: '',
                placeholder: '',
            },

            template: `
        <div class="modal fade">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal">×</button>
                <h3 class="modal-title"></h3>
              </div>
              <div class="modal-body pb-0">
              </div>
              <div class="p-3 pt-0">
                <textarea
                  class="form-control"
                  name="deny-reason"
                  autocomplete="off"
                  type="text"
                  id="deny-organization-reason"
                ></textarea>
              </div>
              <div class="modal-footer">
                <button class="btn btn-default btn-cancel"></button>
                <button class="btn btn-primary"></button>
              </div>
            </div>
          </div>
        </div>
      `,
        },

        /* Sets up the event listeners for the object. Called internally by
         * module.createInstance().
         *
         * Returns nothing.
         */
        initialize: function() {
            jQuery.proxyAll(this, /_on/);
            this.el.on('click', this._onClick);
            console.log('initialized');
        },

        /* Presents the user with a confirm dialogue to ensure that they wish to
         * continue with the current action.
         *
         * Examples
         *
         *   jQuery('.delete').click(function () {
         *     module.confirm();
         *   });
         *
         * Returns nothing.
         */
        confirm: function() {
            this.sandbox.body.append(this.createModal());
            this.modal.modal('show');

            // Center the modal in the middle of the screen.
            this.modal.css({
                'margin-top': this.modal.height() * -0.5,
                top: '50%',
            });
        },

        /* Performs the action for the current item.
         *
         * Returns nothing.
         */
        performAction: function() {
            // get the form on page and add reason and new deny button and click on the button
            const reason = jQuery('#deny-organization-reason').val();
            const form = jQuery.find(
                `form[data-organization="${this.options.org}"]`,
            );
            const inputReason = jQuery('<input />', {
                value: reason,
                name: 'deny-reason',
                required: true,
                class: 'hidden',
            });
            const inputStatus = jQuery('<button />', {
                type: 'submit',
                value: 'denied',
                name: 'approval_status',
                class: 'hidden',
                required: true,
            });
            inputReason.appendTo(form);
            inputStatus.appendTo(form).click();
        },

        /* Creates the modal dialog, attaches event listeners and localised
         * strings.
         *
         * Returns the newly created element.
         */
        createModal: function() {
            if (!this.modal) {
                var element = (this.modal = jQuery(this.options.template));
                element.on('click', '.btn-primary', this._onConfirmSuccess);
                element.on('click', '.btn-cancel', this._onConfirmCancel);
                element.modal({ show: false });

                element
                    .find('.modal-title')
                    .text(this._('Please Confirm Action'));
                var content =
                    this.options.content ||
                    this.options.i18n.content /* Backwards-compatibility */ ||
                    this._('Are you sure you want to perform this action?');
                element.find('.modal-body').text(content);
                element.find('#deny-organization-reason')
                    .attr('placeholder', this.options.placeholder || this.options.i18n.placeholder);
                element.find('.btn-primary').text(this._('Confirm'));
                element.find('.btn-cancel').text(this._('Cancel'));
            }
            return this.modal;
        },

        /* Event handler that displays the confirm dialog */
        _onClick: function(event) {
            event.preventDefault();
            this.confirm();
        },

        /* Event handler for the success event */
        _onConfirmSuccess: function(event) {
            this.performAction();
        },

        /* Event handler for the cancel event */
        _onConfirmCancel: function(event) {
            this.modal.modal('hide');
        },
    };
});
